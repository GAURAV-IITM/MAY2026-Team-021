const DAY_MINUTES = 24 * 60

export function parseTimeToMinutes(time) {
  const [hour = '0', minute = '0'] = String(time || '00:00').split(':')

  return Number(hour) * 60 + Number(minute)
}

export function isSameDayTimeRange(startTime, endTime) {
  return parseTimeToMinutes(endTime) > parseTimeToMinutes(startTime)
}

export function getTimeInterval(startTime, endTime) {
  const start = parseTimeToMinutes(startTime)
  const end = parseTimeToMinutes(endTime)

  return {
    start,
    end,
    wrapsMidnight: end < start,
    isValid: Number.isFinite(start) && Number.isFinite(end) && start !== end,
  }
}

function splitInterval(interval) {
  if (!interval.isValid) return []

  if (!interval.wrapsMidnight) {
    return [{ start: interval.start, end: interval.end }]
  }

  return [
    { start: interval.start, end: DAY_MINUTES },
    { start: 0, end: interval.end },
  ]
}

export function intervalsOverlap(firstInterval, secondInterval) {
  const firstSegments = splitInterval(firstInterval)
  const secondSegments = splitInterval(secondInterval)

  return firstSegments.some((firstSegment) => {
    return secondSegments.some((secondSegment) => {
      return (
        firstSegment.start < secondSegment.end &&
        secondSegment.start < firstSegment.end
      )
    })
  })
}

export function doShiftTimingsOverlap(firstShift, secondShift) {
  return intervalsOverlap(
    getTimeInterval(firstShift.startTime, firstShift.endTime),
    getTimeInterval(secondShift.startTime, secondShift.endTime),
  )
}
