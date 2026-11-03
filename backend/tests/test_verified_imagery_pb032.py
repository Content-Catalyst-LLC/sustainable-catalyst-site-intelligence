"""PB03.2: only synthetic pixels in unit tests; never scientific Wexford observations."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
import verified_imagery_publication_pb032 as m

BOX=[-7.1,52.05,-6.05,52.86]
STAC="S2B_MSIL2A_20260926T114349_N0513_R123_T29UPU_20260926T160226"

@pytest.fixture
def sample(tmp_path):
    # Artificial, unmistakably synthetic gradient, never represented as satellite imagery.
    x=np.linspace(1,255,96,dtype=np.uint8); y=np.linspace(1,255,80,dtype=np.uint8)
    rgb=np.zeros((80,96,3),dtype=np.uint8)
    rgb[:,:,0]=x[None,:];rgb[:,:,1]=y[:,None];rgb[:,:,2]=45
    path=tmp_path/"SYNTHETIC_NOT_WEXFORD.png"
    Image.fromarray(rgb,"RGB").save(path)
    sha=m.sha256_file(path)
    prov=tmp_path/"upstream.json"
    prov.write_text(json.dumps({"request_id":"synthetic-test","access_token":"DO_NOT_EMIT_PRIVATE_TOKENS"}))
    return path,sha,prov


def params(sample):
    img,sha,prov=sample
    return dict(expected_sha256=sha,bbox=BOX,acquisition_date="2026-09-26",selected_stac_reference=STAC,provenance_file=prov)


def test_original_png_verified(sample):
    img,sha,_=sample
    data=m.inspect_source(img,**params(sample))
    assert data["source_sha256"]==sha
    assert data["source_dimensions"]==[96,80]
    assert data["process_type"]=="day-level leastCC mosaic"
    assert data["exact_stac_pixel_identity_proven"] is False


def test_cannot_use_wrong_sha(sample):
    img,_,_=sample
    with pytest.raises(m.SourceError,match="mismatch"):
        m.inspect_source(img,**(params(sample)|{"expected_sha256":"0"*64}))


def test_sha_format_invalid(sample):
    with pytest.raises(m.SourceError,match="SHA-256"):
        m.inspect_source(sample[0],**(params(sample)|{"expected_sha256":"bad"}))


def test_non_png_rejected(sample,tmp_path):
    data=tmp_path/"source.jpg"
    Image.new("RGB",(96,80)).save(data)
    with pytest.raises(m.SourceError,match="PNG"):
        m.inspect_source(data,**(params(sample)|{"expected_sha256":m.sha256_file(data)}))


@pytest.mark.parametrize("bbox",[[100,0,-20,5],[-200,0,-7,5],[-7,80,-6,98],[-7,0,float('nan'),5],[0,0,50,50],"west"])
def test_bad_bbox_rejected(bbox):
    with pytest.raises(m.SourceError):m.check_bbox(bbox)


def test_valid_bbox():
    assert m.check_bbox(BOX)==tuple(BOX)


def test_source_id_validation(sample):
    with pytest.raises(m.SourceError):
        m.inspect_source(sample[0],**(params(sample)|{"selected_stac_reference":"../../bad"}))


def test_non_iso_date_rejected(sample):
    with pytest.raises(m.SourceError):
        m.inspect_source(sample[0],**(params(sample)|{"acquisition_date":"2026-02-30"}))


def test_untrusted_provenance_not_released(sample,tmp_path):
    out=tmp_path/"render"
    m.render_review_figure(sample[0],out,**params(sample))
    j=(out/"FIG-GEO01-manifest.json").read_text()
    assert "DO_NOT_EMIT_PRIVATE_TOKENS" not in j
    assert json.loads(j)["publication"]["eligible"] is False


def test_georectified_preview_and_handoff(sample,tmp_path):
    import rasterio
    out=tmp_path/"realistic_renderer_synthetic"
    result=m.render_review_figure(sample[0],out,**params(sample))
    assert result["display"]["derived_crs"]=="EPSG:32629"
    assert result["display"]["not_native_10m_sentinel_bands"] is True
    assert all((out/rec["name"]).is_file() and m.sha256_file(out/rec["name"])==rec["sha256"] for rec in result["assets"].values())
    with rasterio.open(out/"context_georectified_EPSG32629.tif") as ds:
        assert ds.crs.to_epsg()==32629 and ds.count==4
        assert ds.width>0 and ds.height>0
        assert abs(ds.transform.a)>1  # no fabricated native 10m resolution claim
    handoff=json.loads((out/"FIG-GEO01-publication-handoff.json").read_text())
    assert handoff["projectOwnerVerified"] is False
    assert handoff["publicationEligible"] is False


def test_missing_cloud_mask_not_claimed(sample,tmp_path):
    mfest=m.render_review_figure(sample[0],tmp_path/"render",**params(sample))
    assert mfest["quality"]["scl"]["cloud_fraction_of_valid"] is None
    assert mfest["quality"]["scl"]["state"]=="NOT_ACQUIRED"


def test_quality_counts_from_actual_class_labels():
    vals=np.array([[4,8,9,10,3],[4,0,1,4,4]],dtype=np.uint8)
    res=m.quality_from_scl(vals,paired_response_verified=False)
    assert res["pixel_count"]==10 and res["valid_fraction"]==.8
    assert res["cloud_fraction_of_valid"]==.375
    assert res["shadow_fraction_of_valid"]==.125
    assert res["cloud_and_shadow_fraction_of_valid"]==.5
    assert res["quality_threshold_pass"] is False
    assert res["state"]=="UNPAIRED_REVIEW_ONLY"


def test_unknown_class_fails():
    with pytest.raises(m.SourceError,match="classes"):
        m.quality_from_scl(np.array([[99]],dtype=np.uint8),paired_response_verified=False)


def test_quality_requires_integer_class():
    with pytest.raises(m.SourceError,match="integer"):
        m.quality_from_scl(np.array([[4.0]]),paired_response_verified=False)


def test_quality_can_pass_paired_label_but_not_operator_claim():
    res=m.quality_from_scl(np.full((10,10),4,dtype=np.uint8),paired_response_verified=True)
    assert res["quality_threshold_pass"] is True
    assert res["paired_source_proof"] is True


def test_quality_fails_low_valid_coverage():
    a=np.full((10,10),0,dtype=np.uint8);a[:3,:]=4
    res=m.quality_from_scl(a,paired_response_verified=False)
    assert res["quality_threshold_pass"] is False


def test_scl_unmatched_grid_fails(sample,tmp_path):
    import rasterio
    from rasterio.transform import from_bounds
    p=tmp_path/"wronggrid.tif"
    with rasterio.open(p,"w",driver="GTiff",width=96,height=80,count=1,dtype="uint8",crs="EPSG:4326",transform=from_bounds(-9,52,-8,53,96,80)) as ds:
        ds.write(np.full((80,96),4,dtype=np.uint8),1)
    with pytest.raises(m.SourceError,match="geotransform"):
        m.render_review_figure(sample[0],tmp_path/"render",scl_tif=p,**params(sample))


def test_scl_is_review_only_even_if_claimed_pair(sample,tmp_path):
    import rasterio
    from rasterio.transform import from_bounds
    p=tmp_path/"scl.tif"
    with rasterio.open(p,"w",driver="GTiff",width=96,height=80,count=1,dtype="uint8",crs="EPSG:4326",transform=from_bounds(*BOX,96,80)) as ds:
        ds.write(np.full((80,96),4,dtype=np.uint8),1)
    proof=tmp_path/"paired.json"
    proof.write_text(json.dumps({"source_sha256":sample[1],"scl_sha256":m.sha256_file(p),"same_process_response":True,"response_id":"synthetic"}))
    res=m.render_review_figure(sample[0],tmp_path/"render",scl_tif=p,scl_paired_provenance=proof,**params(sample))
    assert res["quality"]["scl"]["same_response_evidence_declared"] is True
    assert res["quality"]["scl"]["paired_source_proof"] is False
    assert res["publication"]["eligible"] is False


def test_boundary_requires_sha(sample,tmp_path):
    p=tmp_path/"fake.geojson";p.write_text('{}')
    with pytest.raises(m.SourceError,match="SHA-256"):
        m.render_review_figure(sample[0],tmp_path/"render",boundary_geojson=p,**params(sample))


def test_boundary_bad_geometry_fails(sample,tmp_path):
    p=tmp_path/"fake.geojson";p.write_text(json.dumps({"type":"FeatureCollection","features":[]}))
    with pytest.raises(m.SourceError,match="no features"):
        m.render_review_figure(sample[0],tmp_path/"render",boundary_geojson=p,boundary_sha256=m.sha256_file(p),**params(sample))


def test_second_region_automatic_utm_zone(sample,tmp_path):
    # Core renderer can also provide context imagery outside Ireland, though
    # source/provider and research rights are still reviewed separately.
    kwargs=params(sample)|{"bbox":[1.0,48.0,2.0,49.0],"region_label":"Example region B","figure_id":"FIG-OTHER01"}
    mfest=m.render_review_figure(sample[0],tmp_path/"other_region",**kwargs)
    assert mfest["display"]["derived_crs"]=="EPSG:32631"
    assert mfest["figure_id"]=="FIG-OTHER01"
    assert (tmp_path/"other_region"/"FIG-OTHER01_region_context_REVIEW.png").exists()
    assert mfest["publication"]["eligible"] is False