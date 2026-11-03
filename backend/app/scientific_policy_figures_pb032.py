"""Data-driven scientific figure composition for RD-01.4 PB01 and future research.

Works from reviewed structured research assertions, never from a hidden model or
invented per-hectare coefficients. Output is a publication *candidate* until
signed project ownership and editorial/source approval are established.
"""
from __future__ import annotations

import hashlib
import json
import textwrap
from pathlib import Path

SCHEMA="sc-policy-scientific-figures/1.0"


def _wrap(value: str, width: int) -> str:
    return "\n".join(textwrap.wrap(value,width=width,break_long_words=False,break_on_hyphens=False))


def _check_register(data: dict) -> None:
    if data.get("schema") != "sc-policy-field-evidence-register/1.0":
        raise ValueError("Expected structured evidence register/1.0")
    studies=data.get("studies")
    if not isinstance(studies,list) or not (2<=len(studies)<=5):
        raise ValueError("Between 2 and 5 field studies required")
    ids=[]
    for row in studies:
        for key in ("id","location","material","period","endpoint","result","citation","doi","interpretation_limit"):
            if not isinstance(row.get(key),str) or not row[key].strip():
                raise ValueError(f"Study {key} field required")
        if not row["doi"].startswith("10."):
            raise ValueError("Study DOI must be supplied")
        ids.append(row["id"])
    if len(ids)!=len(set(ids)):
        raise ValueError("Duplicate study identifiers")
    if not data.get("cross_study_warning"):
        raise ValueError("Cross-study transferability warning is required")


def render_policy_figures(register_file: str | Path, output_dir: str | Path) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    p=Path(register_file)
    data=json.loads(p.read_text(encoding="utf-8"))
    _check_register(data)
    out=Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)

    # Evidence matrix, not a misleading common scale: endpoints, materials and
    # time frames differ by source. Values are quoted in study-specific units.
    fig, ax=plt.subplots(figsize=(10.1,5.45))
    fig.patch.set_facecolor("white")
    ax.axis("off"); ax.set_xlim(0,10);ax.set_ylim(0,5.25)
    ax.text(.18,5.02,"FIG-PB01  |  International field evidence is heterogeneous",fontsize=16,weight="bold",va="top")
    ax.text(.18,4.59,"Material, treatment duration and endpoint are NOT interchangeable",fontsize=10,va="top")
    y=4.2
    for i,row in enumerate(data["studies"]):
        height=1.0
        rect=FancyBboxPatch((.15,y-height),9.7,height-.07,boxstyle="round,pad=0.01,rounding_size=0.05",
                    linewidth=.8,edgecolor="0.55",facecolor="0.96" if i%2==0 else "white")
        ax.add_patch(rect)
        ax.text(.33,y-.18,_wrap(row["location"],23)+"\n"+_wrap(row["period"],23),fontsize=9.1,weight="bold",va="top")
        ax.text(3.15,y-.18,_wrap(row["material"],38)+"\n"+_wrap(row["endpoint"],38),fontsize=8.5,va="top")
        ax.text(7.12,y-.15,_wrap(row["result"],28),fontsize=8.6,weight="bold",va="top")
        ax.text(7.12,y-.63,_wrap(row["interpretation_limit"],36),fontsize=7.1,va="top")
        y-=1.08
    ax.text(.18,.62,_wrap(data["cross_study_warning"],128),fontsize=9,weight="bold",va="top")
    ax.text(.18,.26,"Sources: "+"; ".join(f"{s['citation']} ({s['doi']})" for s in data["studies"]),fontsize=7.3,va="top")
    fig.tight_layout(pad=.5)
    png1=out/"FIG-PB01-international-field-evidence.png"; svg1=out/"FIG-PB01-international-field-evidence.svg"
    fig.savefig(png1,dpi=230);fig.savefig(svg1);plt.close(fig)

    # Explicit measurement pathway: not the same thing as a weathering-to-CDR assertion.
    steps=[
      ("Source / treatment", "Basalt chemistry, particle size, rate;\napplication & transport records"),
      ("Controls & baseline", "Replicated untreated controls; soil\nchemistry, drainage and pre-treatment data"),
      ("Weathering evidence", "Cation release, pH, alkalinity;\nnon-carbonic acid corrections"),
      ("Carbon fate", "Bicarbonate / DIC export and possible\ndownstream degassing or precipitation"),
      ("Net additional durable CDR", "Subtract crushing, transport, spreading\nand other lifecycle emissions; audit uncertainty"),
      ("Independent MRV", "Replicate, archive, review; credit only\nwhen atmospheric removal is verified")
    ]
    fig,ax=plt.subplots(figsize=(10.2,5.8));fig.patch.set_facecolor("white");ax.axis("off")
    ax.set_xlim(0,10);ax.set_ylim(0,5.9)
    ax.text(.25,5.7,"FIG-PB02  |  Evidence-gated Wexford ERW verification",fontsize=15,weight="bold",va="top")
    ax.text(.25,5.34,"Conceptual monitoring pathway — NOT a measured Wexford carbon removal result",fontsize=9.4,va="top")
    coords=[(.35,3.9),(3.55,3.9),(6.75,3.9),(.35,1.65),(3.55,1.65),(6.75,1.65)]
    for i,((head,desc),(x,y)) in enumerate(zip(steps,coords)):
        patch=FancyBboxPatch((x,y),2.8,1.12,boxstyle="round,pad=.08,rounding_size=.07",linewidth=1,edgecolor="0.5",facecolor="0.97")
        ax.add_patch(patch)
        ax.text(x+.12,y+.97,head,fontsize=10,weight="bold",va="top")
        ax.text(x+.12,y+.66,desc,fontsize=7.9,va="top")
    def arrow(start,end):
        ax.add_patch(FancyArrowPatch(start,end,arrowstyle="->",mutation_scale=13,linewidth=1.35,color="0.28",connectionstyle="arc3,rad=0"))
    arrow((3.19,4.46),(3.47,4.46));arrow((6.39,4.46),(6.67,4.46))
    arrow((8.15,3.85),(8.15,3.0));arrow((8.15,3.0),(1.75,3.0));arrow((1.75,3.0),(1.75,2.86))
    arrow((3.19,2.21),(3.47,2.21));arrow((6.39,2.21),(6.67,2.21))
    ax.text(.28,.88,"Policy gate: fund controlled pilots first; expand only after verified net additional durable removal.",fontsize=10,weight="bold")
    ax.text(.28,.51,"Distinct evidence domains: reaction chemistry ≠ alkalinity delivery ≠ verified atmospheric net CO₂ removal.",fontsize=9)
    ax.text(.28,.24,"Sustainable Catalyst · Research Lab / Workbench / Site Intelligence → Publication Studio",fontsize=8)
    fig.tight_layout(pad=.65)
    png2=out/"FIG-PB02-carbon-removal-MRV-pathway.png";svg2=out/"FIG-PB02-carbon-removal-MRV-pathway.svg"
    fig.savefig(png2,dpi=230);fig.savefig(svg2);plt.close(fig)

    def info(path):
        b=path.read_bytes();return {"filename":path.name,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
    m={"schema":SCHEMA,"source_register":info(p),
      "figures":{"FIG-PB01":{"png":info(png1),"svg":info(svg1),"data_classification":"cross-study evidence matrix, no pooled effect estimate"},
                 "FIG-PB02":{"png":info(png2),"svg":info(svg2),"data_classification":"conceptual MRV, no computed removal"}},
      "publication":{"eligible":False,"editorial_review":"PENDING","signed_project_binding":"NOT_PERFORMED"},
      "reuse":"any research domain with 2–5 appropriately cited study assertions; diagram template can be specialized"}
    (out/"FIG-PB01-PB02-manifest.json").write_text(json.dumps(m,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return m