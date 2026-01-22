import roserer.dust.dust_system as ds
import roserer.ros2system as ros
import roserer.systemvalidator as validator





############################----VALIDATION----############################

####All templates
# id's must be unique (with respect to other callbacks of same type under same executor, and between executors)


####All callbacks
# INVARIANT: Timer-buffer size 1?
# is the type-parameter within bounds (0 - 3)
# two last arrays should (probably/preferably) be all 0 when no subscribers
# the release-times for subscribers should be (weakly?) increasing
# all referenced id's should correspond to something (maybe checked in validator already?)
# if Timer-type, then buffersize should be 1


#### datacallback
# can not be a timer-callback?


####Sporadic callback
# INVARIANT: length must correspond to non-zero values in releases-array (except if first is zero?)

####Periodic callback
# invariant: period should be less than execution-time -> else overflow is more or less guaranteed?
