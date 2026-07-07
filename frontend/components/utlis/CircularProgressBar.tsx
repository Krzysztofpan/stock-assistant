import { cn } from "@/lib/utils"

export type CircularProgressBarProps = {
  percentage: number
  size?: number
  strokeWidth?: number
  trackColor?: string
  progressColor?: string
  warningColor?: string
  completeColor?: string
  warningThreshold?: number
  /** Show center label. "auto" shows when percentage >= warningThreshold */
  showLabel?: boolean | "auto"
  label?: React.ReactNode | ((percentage: number) => React.ReactNode)
  labelColor?: string
  completeLabelColor?: string
  animateOnWarning?: boolean
  /** true uses scale-125, number sets custom scale factor */
  scaleOnWarning?: boolean | number
  warningAnimationClass?: string
  className?: string
  svgClassName?: string
  transitionDuration?: string
}

const DEFAULT_SIZE = 30

const CircularProgressBar = ({
  percentage,
  size = DEFAULT_SIZE,
  strokeWidth = 2,
  trackColor = "rgb(61, 61, 61)",
  progressColor = "rgb(0, 140, 255)",
  warningColor = "rgb(255, 230, 0)",
  completeColor = "rgb(255, 0, 0)",
  warningThreshold = 92.8,
  showLabel = "auto",
  label,
  labelColor = "white",
  completeLabelColor = "red",
  animateOnWarning = true,
  scaleOnWarning = true,
  warningAnimationClass = "animate-yellow",
  className,
  svgClassName,
  transitionDuration = "0.5s",
}: CircularProgressBarProps) => {
  const clampedPercentage = Math.min(100, Math.max(0, percentage))
  const center = size / 2
  const scaleFactor = size / DEFAULT_SIZE
  const isWarning = clampedPercentage >= warningThreshold
  const isComplete = clampedPercentage === 100

  const radius = (isWarning ? 13 : 11) * scaleFactor
  const normalizedRadius = radius - strokeWidth * 0.5
  const circumference = normalizedRadius * 2 * Math.PI
  const strokeDashoffset
    = circumference - (clampedPercentage / 100) * circumference

  const progressStroke = isComplete
    ? completeColor
    : isWarning
      ? warningColor
      : progressColor

  const shouldShowLabel
    = showLabel === "auto" ? isWarning : showLabel

  const labelContent
    = label !== undefined
      ? typeof label === "function"
        ? label(clampedPercentage)
        : label
      : 280 - clampedPercentage * 2.8

  const scaleStyle
    = isWarning && scaleOnWarning
      ? {
          transform: `scale(${typeof scaleOnWarning === "number" ? scaleOnWarning : 1.25})`,
        }
      : undefined

  return (
    <div
      className={cn(
        "flex items-center justify-center transition-all",
        className,
      )}
      style={scaleStyle}
    >
      <svg
        height={size}
        width={size}
        className={cn(
          "transition-all",
          isWarning && animateOnWarning && warningAnimationClass,
          svgClassName,
        )}
      >
        <circle
          stroke={trackColor}
          fill="transparent"
          strokeWidth={strokeWidth}
          r={normalizedRadius}
          cx={center}
          cy={center}
        />
        <circle
          stroke={progressStroke}
          className="transition-all"
          fill="transparent"
          strokeWidth={strokeWidth}
          r={normalizedRadius}
          cx={center}
          cy={center}
          style={{
            strokeDasharray: circumference,
            strokeDashoffset,
            transform: "rotate(-90deg)",
            transformOrigin: "50% 50%",
            transition: `stroke-dashoffset ${transitionDuration} ease, stroke 0.3s ease`,
          }}
        />
        {shouldShowLabel
          ? (
              <text
                x="50%"
                y="50%"
                textAnchor="middle"
                dy=".3em"
                fontSize={10 * scaleFactor}
                fill={isComplete ? completeLabelColor : labelColor}
              >
                {labelContent}
              </text>
            )
          : null}
      </svg>
    </div>
  )
}

export default CircularProgressBar
