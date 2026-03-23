from roserer.adapters.backeman_adapter import transform_system
import roserer.ros2system as ros
import roserer.patterns.backeman as bmp

# Case study has following parameters:
# - cameras: No. of cameras
# - prob: probability of each camera being used (load)
# - mcamera: which camera should be monitored
# - subcription: if True, subscription is used of fusion (otherwise Timer)
#
def case_study(cameras, prob, mcamera, subscription, fusion_period=500):

    CAMERAWCET = 20
    CAMERAPER = 1000
    OBJDETWCET = 50
    FUSIONSUBWCET = 90
    FUSIONSUB = 10
    FUSIONTIMERWCET = 90
    ACTUATORWCET = 50
    
    if mcamera >= cameras:
        return None

    if subscription:
        name = "casestudy" + str(cameras) + "_" + str(mcamera) + "_sub"
    else:
        name = "casestudy" + str(cameras) + "_" + str(mcamera) + "_tmr"

    system = ros.System(name)
    e = system.add_host("host").add_executor("executor")

    for i in range(cameras):
        bmp.add_probabilistic_datagenerator(
                e, "CAMERA" + str(i), CAMERAWCET, CAMERAPER, 0, prob)
        bmp.add_subscriber(e, "OBJDET" + str(i), OBJDETWCET, "CAMERA" + str(i))

    if subscription:
        bmp.add_subscriber(
                e,
                "FUSION",
                FUSIONSUBWCET,
                "OBJDET0",
                ["OBJDET" + str(i) for i in range(1,cameras)],
                [FUSIONSUB]*(cameras-1))
    else:
        bmp.add_timer(
                e,
                "FUSION",
                FUSIONTIMERWCET,
                fusion_period,
                0,
                ["OBJDET" + str(i) for i in range(cameras)],
                [FUSIONSUB]*cameras)
    bmp.add_subscriber(e, "ACTUATOR", ACTUATORWCET, "FUSION")
    bms = transform_system(system, (f"CAMERA{mcamera}", "ACTUATOR"))
    return bms

