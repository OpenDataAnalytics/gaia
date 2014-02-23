def attrib_to_converters(string):
    """Poor man's udunits.
    Give this a udunit's time attribute and it will generate functions to
    convert numbers in that calendar to and from a standard numerical format.
    If returns False on error.
    Note: using udunits is preferable but I haven't yet gotten it to work well on my system.
    """

    if not string or not "since" in string:
        return False
    print string
    parts = string.split("since")
    units = parts[0].strip()

    if (units != "days" and
        units != "weeks" and
        units != "months" and
        units != "years"):
        return False
    print units

    after = parts[1].strip()
    startDate = after.split(" ")[0]
    start_year = int(startDate.split("-")[0])
    start_month = int(startDate.split("-")[1])
    start_day = int(startDate.split("-")[2])
    ylen = 365
    mlen = ylen/12
    mult = 1
    if units == "weeks":
        mult = 7
    if units == "months":
        mult = mlen
    if units == "years":
        mult = ylen

    def localoffset_to_absday(x):
        days = x*mult+start_year*ylen+start_month*mlen+start_day
        return days

    def absday_to_localoffset(d):
        localstart = localoffset_to_absday(0)
        localoffset = d - localstart
        steps = localoffset/mult
        return steps

    def absday_to_ymd(x):
        print "x = ", x
        print "ylen = ", ylen
        year = x/ylen
        month = (x%ylen)/mlen #not quite right this is source of rounding errors
        day = (x%ylen)%mlen
        return year,month,day

    def ymd_to_absday(y,m,d):
        ydays = y*ylen
        mdays = m*mlen
        totaldays = ydays+mdays+d
        return totaldays

    return localoffset_to_absday, absday_to_ymd, units, startDate, ymd_to_absday, absday_to_localoffset

def test_helper(unitspec):
    localizer = attrib_to_converters(unitspec)
    if not localizer:
        print "Problem with " + str(unitspec)
        return False

    local_to_abs = localizer[0]
    abs_to_local = localizer[5]
    abs_to_date = localizer[1]
    date_to_abs = localizer[4]

    abs_d0 = local_to_abs(0)
    abs_d1 = local_to_abs(1)
    abs_d30 = local_to_abs(30)
    abs_dn1 = local_to_abs(-1)
    abs_dn30 = local_to_abs(-30)
    print abs_d0, abs_d1, abs_d30, abs_dn1, abs_dn30

    print abs_to_local(abs_d0), abs_to_local(abs_d1), abs_to_local(abs_d30), abs_to_local(abs_dn1), abs_to_local(abs_dn30)

    date_d0 = abs_to_date(abs_d0)
    date_d1 = abs_to_date(abs_d1)
    date_d30 = abs_to_date(abs_d30)
    date_dn1 = abs_to_date(abs_dn1)
    date_dn30 = abs_to_date(abs_dn30)
    print date_d0, date_d1, date_d30, date_dn1, date_dn30

    print date_to_abs(*date_d0), date_to_abs(*date_d1), date_to_abs(*date_d30), date_to_abs(*date_dn1), date_to_abs(*date_dn30)
    return local_to_abs, abs_to_local, abs_to_date, date_to_abs

def test():
    import time
    """ Start a disco inferno baby! """
    discoizer = test_helper("days since 1970-0-0")
    discoizer2 = test_helper("months since 1970-0-0")
    cltFOREVER = test_helper("months since 1979-1-1 0")

    print "TODAY"
    timenow = time.time() # seconds since epoch
    print timenow
    utcifier = test_helper("days since 1970-0-0")
    todayinAbs = utcifier[0](timenow/(60*60))
    print todayinAbs
    todayinCLT = cltFOREVER[1](todayinAbs)
    print todayinCLT
