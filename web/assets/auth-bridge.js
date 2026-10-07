export const authBridge=Object.freeze({
  mode:"credential-forwarding-ready",
  wordpressRequired:false,
  async status(){
    return {authenticated:false,mode:this.mode,wordpressRequired:false,note:"v4.55.3 provides transport and session boundaries; global authentication remains independently pluggable."};
  }
});
