//VERSION=3
// Paired RGB/SCL/dataMask outputs from ONE Sentinel Hub Process request.
// Never run without separate provider-quota authorization.
function setup() {
  return {
    input: ["B02","B03","B04","SCL","dataMask"],
    output: [
      {id:"rgb",bands:4,sampleType:"AUTO"},
      {id:"scl",bands:1,sampleType:"UINT8"},
      {id:"valid",bands:1,sampleType:"UINT8"}
    ],
    mosaicking:"SIMPLE"
  };
}
function evaluatePixel(sample) {
  return {
    rgb:[2.5*sample.B04,2.5*sample.B03,2.5*sample.B02,sample.dataMask],
    scl:[sample.SCL],
    valid:[sample.dataMask]
  };
}
