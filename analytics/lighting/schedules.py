"""Assumed schedules, independent of attendance and the frozen original baseline."""
import pandas as pd


LEGACY_START_HOUR = 8
LEGACY_END_HOUR = 18


def operating_mask(dates, settings):
    dates = pd.DatetimeIndex(dates)
    return (dates.day_of_week.isin(settings['operating_weekdays']) &
            (dates.hour >= settings['operating_start_hour']) &
            (dates.hour < settings['operating_end_hour']) &
            ~dates.normalize().isin(pd.to_datetime(settings.get('excluded_dates', []))))


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

    # Holiday exclusions are a separate assumption; keep weekday-only comparisons reproducible.
    if settings.get('university_holiday_dates'):
        windows = [('primary', settings)] + [
            (item['id'], {**settings, 'operating_start_hour': item['start_hour'],
                          'operating_end_hour': item['end_hour']})
            for item in settings.get('schedule_sensitivities', [])]
        for name, window in windows:
            yield name + '_holiday_excluded', {**window, 'excluded_dates': settings['university_holiday_dates']}


def label(settings):
    return f"{settings['operating_start_hour']:02d}:00–{settings['operating_end_hour']:02d}:00"


def legacy_settings(settings):
    return {**settings, 'operating_start_hour': LEGACY_START_HOUR,
            'operating_end_hour': LEGACY_END_HOUR}


def transition_mask(dates, settings):
    dates = pd.DatetimeIndex(dates)
    return (dates.day_of_week.isin(settings['operating_weekdays']) &
            (dates.hour >= settings['transition_start_hour']) &
            (dates.hour < settings['transition_end_hour']))
