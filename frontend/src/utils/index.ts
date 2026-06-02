/**
 * 冷链监控平台 - 共享工具函数
 */

import dayjs from 'dayjs'

/** 温控常量 */
export const TEMP_THRESHOLDS = {
  DANGER: 8,   // 高温危险线 (°C)
  WARN: 6,     // 高温预警线 (°C)
  LOW: -25,    // 低温异常线 (°C)
  COMPLIANT_MIN: -25,
  COMPLIANT_MAX: 8,
} as const

/** 温度状态样式类 */
export function getTempClass(temp: number): string {
  if (!temp && temp !== 0) return ''
  if (temp > TEMP_THRESHOLDS.DANGER) return 'temp-danger'
  if (temp > TEMP_THRESHOLDS.WARN) return 'temp-warn'
  return 'temp-normal'
}

/** 格式化时间显示 */
export function formatTime(ts: string): string {
  if (!ts) return '-'
  return dayjs(ts).format('HH:mm:ss')
}

/** 格式化日期时间 (中文) */
export function formatDateTime(ts: string): string {
  if (!ts) return '-'
  return new Date(ts).toLocaleString('zh-CN')
}

/** 风险等级映射 */
export function getRiskType(level: string): string {
  const map: Record<string, string> = { normal: 'success', warning: 'warning', critical: 'danger' }
  return map[level] || 'info'
}

/** 风险等级中文标签 */
export function getRiskLabel(level: string): string {
  const map: Record<string, string> = { normal: '正常', warning: '注意', critical: '危险' }
  return map[level] || level
}
