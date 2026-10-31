package dev.obsidiannetwork.client.animation;

/**
 * v1.7.5 CLIENT-SIDE suit assembly choreography from the uploaded animation patch.
 * Rendering/mesh binding belongs to the host mod; armor ownership is server-side.
 * Model axes are calibrated in GeckoLib per-tier animation assets.
 */
public final class ArmorAssemblyAnimation {
    private ArmorAssemblyAnimation() {}
    public enum Action { EQUIP, UNEQUIP, RECALL_FLIGHT, RECALL_BRAKE, RECALL_DOCK }
    public record Pose(
        double rootPitchDeg, double rootRollDeg,
        double rearLeftYawDeg, double rearRightYawDeg,
        double rearHalfOffsetPx, double upperChestSeparationPx,
        double shoulderFoldDeg, double forearmFoldDeg,
        double thighReleaseDeg,
        double faceplateHingePitchDeg, double faceplateLiftPx,
        double faceplateForwardPx, double thrusterIntensity,
        double latchIntensity, boolean modelVisible
    ) {}
    public interface SuitRig {
        void setRootOrientation(double pitchDegrees,double rollDegrees);
        void setRearHalves(double leftYawDeg,double rightYawDeg,double outwardPx);
        void setChestPlates(double separationPx);
        void setArms(double shoulderFoldDeg,double forearmFoldDeg);
        void setLegs(double thighReleaseDeg);
        void setFaceplate(double hingePitchDeg,double liftPx,double forwardPx);
        void setThrusters(double intensity);
        void setLatchIntensity(double intensity);
        void setVisible(boolean visible);
    }
    public static void apply(SuitRig rig,Pose pose){
        if(rig==null||pose==null)throw new IllegalArgumentException("rig and pose required");
        rig.setRootOrientation(pose.rootPitchDeg(),pose.rootRollDeg());
        rig.setRearHalves(pose.rearLeftYawDeg(),pose.rearRightYawDeg(),pose.rearHalfOffsetPx());
        rig.setChestPlates(pose.upperChestSeparationPx());
        rig.setArms(pose.shoulderFoldDeg(),pose.forearmFoldDeg());
        rig.setLegs(pose.thighReleaseDeg());
        rig.setFaceplate(pose.faceplateHingePitchDeg(),pose.faceplateLiftPx(),pose.faceplateForwardPx());
        rig.setThrusters(pose.thrusterIntensity());
        rig.setLatchIntensity(pose.latchIntensity());
        rig.setVisible(pose.modelVisible());
    }
    public static Pose sample(Action action,double normalizedTime){
        if(action==null)throw new IllegalArgumentException("action required");
        double t=clamp01(normalizedTime);
        double rear=0,mask=0,pitch=0,thrust=0,torso=0,limbs=0,glow=0;
        switch(action){
            case EQUIP -> {
                rear=envelope(t,.06,.29,.55,.82);
                mask=envelope(t,.02,.21,.88,1.00);
                torso=envelope(t,.11,.28,.56,.81);
                limbs=envelope(t,.20,.34,.59,.82);
                glow=smooth(.72,.95,t)*(1-smooth(.96,1,t));
            }
            case UNEQUIP -> {
                mask=envelope(t,.00,.17,.89,1.00);
                rear=envelope(t,.18,.40,.66,.88);
                torso=envelope(t,.20,.39,.68,.86);
                limbs=envelope(t,.24,.43,.65,.87);
                glow=smooth(.77,.96,t)*(1-smooth(.97,1,t));
            }
            case RECALL_FLIGHT -> {pitch=-90;thrust=1.0;}
            case RECALL_BRAKE -> {
                pitch=-90*(1-smooth(.12,.83,t));
                thrust=1-smooth(.52,1,t);
                mask=smooth(.68,1,t);
            }
            case RECALL_DOCK -> {
                mask=1-smooth(.87,1,t);
                rear=envelope(t,.00,.18,.56,.82);
                torso=envelope(t,.05,.21,.59,.82);
                limbs=envelope(t,.08,.25,.65,.84);
                glow=smooth(.69,.96,t)*(1-smooth(.97,1,t));
                thrust=.23*(1-smooth(.08,.29,t));
            }
        }
        return new Pose(pitch,0,-78*rear,78*rear,2.6*rear,1.3*torso,
            13*limbs,9*limbs,11*limbs,-108*mask,2*mask,1.5*mask,
            thrust,glow,true);
    }
    /** Pure visual easing: actual physics/arrival remain server-authoritative. */
    public static FlightFrame recallFlight(Vec3 start,Vec3 end,double progress,double bankDeg){
        if(start==null||end==null)throw new IllegalArgumentException("start/end required");
        double t=clamp01(progress);
        Vec3 pos=start.lerp(end,smooth(0,1,t));
        double dx=end.x()-start.x(),dz=end.z()-start.z();
        double yaw=Math.toDegrees(Math.atan2(-dx,dz));
        double bank=Math.max(-18,Math.min(18,bankDeg))*Math.sin(Math.PI*t);
        double power=.70+.30*Math.sin(Math.PI*t);
        return new FlightFrame(pos,yaw,-90,bank,power);
    }
    public record Vec3(double x,double y,double z){
        public Vec3 lerp(Vec3 b,double t){
            return new Vec3(x+(b.x-x)*t,y+(b.y-y)*t,z+(b.z-z)*t);
        }
    }
    public record FlightFrame(Vec3 position,double yawDeg,double pitchDeg,
                              double rollDeg,double thrusterIntensity){}
    private static double envelope(double t,double a,double b,double c,double d){
        return smooth(a,b,t)*(1-smooth(c,d,t));
    }
    private static double clamp01(double v){
        return !Double.isFinite(v)?0:Math.max(0,Math.min(1,v));
    }
    private static double smooth(double a,double b,double t){
        double x=clamp01((t-a)/(b-a));
        return x*x*(3-2*x);
    }
}
