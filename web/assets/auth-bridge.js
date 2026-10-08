export const authBridge=Object.freeze({
  mode:"credential-forwarding-ready",
  wordpressRequired:false,
  async status(){
    return {authenticated:false,mode:this.mode,wordpressRequired:false,note:"v4.55.3.2.2 preserves the standalone transport/session boundary while API reliability is certified independently."};
  }
});
