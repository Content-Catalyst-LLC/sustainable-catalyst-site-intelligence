export const authBridge=Object.freeze({
  mode:"credential-forwarding-ready",
  wordpressRequired:false,
  async status(){
    return {authenticated:false,mode:this.mode,wordpressRequired:false,note:"v4.56.0 preserves the standalone transport/session boundary while API reliability is certified independently."};
  }
});
