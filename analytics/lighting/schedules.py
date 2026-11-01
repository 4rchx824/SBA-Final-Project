"""Assumed schedules, independent of attendance and the frozen original baseline."""
import pandas as pd


LEGACY_START_HOUR = 8
LEGACY_END_HOUR = 18


def operating_mask(dates, settings):
    dates = pd.DatetimeIndex(dates)
    return (dates.dayofweek.isin(settings['operating_weekdays']) &
            (dates.hour >= settings['operating_start_hour']) &
            (dates.hour < settings['operating_end_hour']))


def operating_index(settings, start, end):
    dates = pd.date_range(start, end, freq='15min', inclusive='left')
    return dates[operating_mask(dates, settings)]


def schedule_settings(settings):
    """Primary first; each sensitivity recalibrates March independently."""
    yield 'primary', settings
    for schedule in settings.get('schedule_sensitivities', []):
        yield schedule['id'], {**settings,
                              'operating_start_hour': schedule['start_hour'],
                              'operating_end_hour': schedule['end_hour']}


def label(settings):
    return f"{settings['operating_start_hour']:02d}:00–{settings['operating_end_hour']:02d}:00"


def legacy_settings(settings):
    return {**settings, 'operating_start_hour': LEGACY_START_HOUR,
            'operating_end_hour': LEGACY_END_HOUR}


def transition_mask(dates, settings):
    dates = pd.DatetimeIndex(dates)
    return (dates.dayofweek.isin(settings['operating_weekdays']) &
            (dates.hour >= settings['transition_start_hour']) &
            (dates.hour < settings['transition_end_hour']))
