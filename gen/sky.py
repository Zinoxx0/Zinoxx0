"""The real sky over Lisbon, worked out with plain maths.

sun_times() is NOAA's solar calculator and moon() the mean-lunation series from Meeus' Astronomical
Algorithms, so the daily build needs no network for either. The hero's bar shows today's values and
its night scene draws today's moon.
"""
import datetime as dt
import math
from zoneinfo import ZoneInfo

LISBON = (38.7223, -9.1393)
TZ = ZoneInfo("Europe/Lisbon")
SYNODIC = 29.530588853         # days from new moon to new moon


def _rad(d):
    return math.radians(d)


def _deg(r):
    return math.degrees(r)


def _solar(jc):
    """Equation of time (minutes) and declination (degrees) at jc Julian centuries since J2000."""
    l0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360
    m = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    c = (math.sin(_rad(m)) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
         + math.sin(_rad(2 * m)) * (0.019993 - 0.000101 * jc)
         + math.sin(_rad(3 * m)) * 0.000289)
    lon = l0 + c - 0.00569 - 0.00478 * math.sin(_rad(125.04 - 1934.136 * jc))
    eps = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60
    eps += 0.00256 * math.cos(_rad(125.04 - 1934.136 * jc))
    decl = _deg(math.asin(math.sin(_rad(eps)) * math.sin(_rad(lon))))
    y = math.tan(_rad(eps / 2)) ** 2
    eot = 4 * _deg(y * math.sin(2 * _rad(l0)) - 2 * e * math.sin(_rad(m))
                   + 4 * e * y * math.sin(_rad(m)) * math.cos(2 * _rad(l0))
                   - 0.5 * y * y * math.sin(4 * _rad(l0)) - 1.25 * e * e * math.sin(2 * _rad(m)))
    return eot, decl


def sun_times(day, lat=LISBON[0], lon=LISBON[1], tz=TZ):
    """Sunrise and sunset on `day` as aware datetimes in tz, or None near the poles."""
    jd = day.toordinal() + 1721424.5 + 0.5 - lon / 360
    out = []
    for sign in (-1, 1):
        minutes = 720.0
        for _ in range(3):             # the sun's position barely moves, so this settles at once
            jc = (jd + minutes / 1440 - 0.5 - 2451545) / 36525
            eot, decl = _solar(jc)
            cos_h = ((math.cos(_rad(90.833)) - math.sin(_rad(lat)) * math.sin(_rad(decl)))
                     / (math.cos(_rad(lat)) * math.cos(_rad(decl))))
            if abs(cos_h) > 1:
                return None
            minutes = 720 - 4 * lon - eot + sign * 4 * _deg(math.acos(cos_h))
        utc = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc) + dt.timedelta(minutes=minutes)
        out.append(utc.astimezone(tz))
    return tuple(out)


def _new_moon(k):
    """Julian day of mean lunation k, with the largest periodic terms (Meeus ch. 49), good to minutes."""
    t = k / 1236.85
    jde = 2451550.09766 + 29.530588861 * k + 0.00015437 * t * t
    e = 1 - 0.002516 * t - 0.0000074 * t * t
    m = _rad(2.5534 + 29.10535670 * k)
    mp = _rad(201.5643 + 385.81693528 * k)
    f = _rad(160.7108 + 390.67050284 * k)
    return jde + (-0.40720 * math.sin(mp) + 0.17241 * e * math.sin(m) + 0.01608 * math.sin(2 * mp)
                  + 0.01039 * math.sin(2 * f) + 0.00739 * e * math.sin(mp - m)
                  - 0.00514 * e * math.sin(mp + m) + 0.00208 * e * e * math.sin(2 * m))


def moon(when):
    """{'age', 'phase' (0 new .. 0.5 full .. 1 new), 'lit' (0..1), 'name'} for an aware datetime."""
    jd = when.timestamp() / 86400 + 2440587.5
    k = math.floor((jd - 2451550.09766) / SYNODIC)
    # the mean estimate can land a lunation off, so step to the real pair around jd
    while _new_moon(k) > jd:
        k -= 1
    while _new_moon(k + 1) <= jd:
        k += 1
    start, end = _new_moon(k), _new_moon(k + 1)
    age = jd - start
    phase = age / (end - start)
    lit = (1 - math.cos(2 * math.pi * phase)) / 2
    return {"age": age, "phase": phase, "lit": lit, "name": _phase_name(phase)}


def _phase_name(p):
    names = ("New moon", "Waxing crescent", "First quarter", "Waxing gibbous",
             "Full moon", "Waning gibbous", "Last quarter", "Waning crescent")
    return names[math.floor(p * 8 + 0.5) % 8]
