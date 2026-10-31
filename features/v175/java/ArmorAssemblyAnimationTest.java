package dev.obsidiannetwork.client.animation;
public final class ArmorAssemblyAnimationTest {
    private static void check(boolean ok,String msg){if(!ok)throw new AssertionError(msg);}
    private static void near(double a,double b,String msg){check(Math.abs(a-b)<1e-8,msg+" "+a+" != "+b);}
    public static void main(String[] args){
        for(int i=0;i<=100;i++){
            double t=i/100.0;
            var flight=ArmorAssemblyAnimation.sample(ArmorAssemblyAnimation.Action.RECALL_FLIGHT,t);
            near(flight.rootPitchDeg(),-90,"horizontal recall");
            check(flight.thrusterIntensity()>.95,"recall thrust");
            for(var a:ArmorAssemblyAnimation.Action.values()){
                var pose=ArmorAssemblyAnimation.sample(a,t);
                check(Double.isFinite(pose.faceplateHingePitchDeg()),"faceplate finite");
                near(pose.rearLeftYawDeg(),-pose.rearRightYawDeg(),"symmetric split");
            }
        }
        var a=ArmorAssemblyAnimation.sample(ArmorAssemblyAnimation.Action.RECALL_DOCK,.85);
        var b=ArmorAssemblyAnimation.sample(ArmorAssemblyAnimation.Action.RECALL_DOCK,.90);
        check(Math.abs(a.rearLeftYawDeg())<.001,"rear closes before faceplate");
        check(b.faceplateHingePitchDeg()<-1,"mask last");
        var end=ArmorAssemblyAnimation.sample(ArmorAssemblyAnimation.Action.RECALL_DOCK,1);
        near(end.rearLeftYawDeg(),0,"body closed");
        near(end.faceplateHingePitchDeg(),0,"mask closed");
        check(Math.abs(ArmorAssemblyAnimation.sample(ArmorAssemblyAnimation.Action.UNEQUIP,.55)
              .rearLeftYawDeg())>70,"rear half opens on exit");
        near(ArmorAssemblyAnimation.sample(ArmorAssemblyAnimation.Action.RECALL_BRAKE,1)
              .rootPitchDeg(),0,"brake upright");
        var f0=ArmorAssemblyAnimation.recallFlight(
             new ArmorAssemblyAnimation.Vec3(0,2,0),
             new ArmorAssemblyAnimation.Vec3(5,3,0),0,8);
        var f1=ArmorAssemblyAnimation.recallFlight(
             new ArmorAssemblyAnimation.Vec3(0,2,0),
             new ArmorAssemblyAnimation.Vec3(5,3,0),1,8);
        near(f0.position().x(),0,"flight start");
        near(f1.position().x(),5,"flight end");
        near(f1.pitchDeg(),-90,"horizontal until arrival");
        System.out.println("V175_JAVA_CHOREOGRAPHY_STANDALONE_PASS");
    }
}
