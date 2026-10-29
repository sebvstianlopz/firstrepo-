"use client";

import * as React from "react";
import { useMotionValueEvent, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { cn } from "@/lib/utils";

interface ScrollFlyInProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Content in the middle of the stage: static, or revealed by the image when `reveal` is set. */
  children: React.ReactNode;
  imageUrl: string;
  imageAlt?: string;
  /** Full-bleed layer behind everything, such as a photo. */
  background?: React.ReactNode;
  /** Layer that fades out as the image arrives, such as a "scroll" cue. */
  hint?: React.ReactNode;
  /** Wipe the children into view behind the image as it passes. */
  reveal?: boolean;
  /** Where the wipe edge sits inside the image, as a fraction of its width (0 = its left edge). */
  revealAt?: number;
  /** Classes for the flying image. Set its width with the `--fly-w` variable, e.g. `[--fly-w:70%]`. */
  imageClassName?: string;
  stickyClassName?: string;
}

/*
  One motion value, `--p` (0 → 1 over the scroll), drives everything in CSS:
  the image's left edge travels from `-W` (fully off-screen left) to `100%`
  (fully off-screen right), where W is `--fly-w` (60% unless CSS sets it). Working in
  percentages keeps the first render correct on the server, where there is no window to measure.
*/
const W = "var(--fly-w, 60%)";
const IMAGE_LEFT = `calc(var(--p) * (100% + ${W}) - ${W})`;
// The reveal edge: where the image's rear sits (`revealAt` of its width).
const EDGE = `(${IMAGE_LEFT} + var(--reveal-at) * ${W})`;
// Content fades in over this band behind the edge instead of appearing along a hard line.
// It narrows to nothing as the image leaves, so everything ends fully visible.
const FEATHER = `(var(--reveal-feather, 22%) * (1 - var(--p)))`;
const REVEAL_MASK = `linear-gradient(to right, #000 calc(${EDGE} - ${FEATHER}), transparent calc(${EDGE}))`;

const ScrollFlyIn = React.forwardRef<HTMLDivElement, ScrollFlyInProps>(
  (
    {
      children,
      imageUrl,
      imageAlt = "Animated image",
      background,
      hint,
      reveal = false,
      revealAt = 0,
      className,
      imageClassName,
      stickyClassName,
      style,
      ...props
    },
    ref,
  ) => {
    const targetRef = React.useRef<HTMLDivElement>(null);
    React.useImperativeHandle(ref, () => targetRef.current as HTMLDivElement);
    const reduceMotion = useReducedMotion();

    const { scrollYProgress } = useScroll({
      target: targetRef,
      offset: ["start start", "end end"],
    });

    // Short hold at both ends, so the start and the fully revealed state both rest a moment.
    const p = useTransform(scrollYProgress, [0.04, 0.82], [0, 1], { clamp: true });
    const hintOpacity = useTransform(scrollYProgress, [0, 0.12], [1, 0]);

    // Write the values straight to CSS: no re-renders, and no need for framer's <motion.*> bundle.
    const stageRef = React.useRef<HTMLDivElement>(null);
    const hintRef = React.useRef<HTMLDivElement>(null);
    useMotionValueEvent(p, "change", (v) => stageRef.current?.style.setProperty("--p", String(v)));
    useMotionValueEvent(hintOpacity, "change", (v) => {
      if (hintRef.current) hintRef.current.style.opacity = String(v);
    });

    if (reduceMotion) {
      return (
        <div ref={targetRef} className={cn("relative", className, "h-auto")} style={style} {...props}>
          {/* Same stage size as the animated version, but static and fully revealed. */}
          <div
            className={cn("relative flex h-screen items-center justify-center overflow-hidden", stickyClassName)}
            style={{ position: "relative", top: 0 }}
          >
            {background && <div className="absolute inset-0">{background}</div>}
            <div className="absolute inset-0 z-10" data-fly-content>
              {children}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div
        ref={targetRef}
        className={cn("relative h-[200vh]", className)}
        style={{ "--reveal-at": revealAt, ...style } as React.CSSProperties}
        {...props}
      >
        <div
          ref={stageRef}
          className={cn("sticky top-0 flex h-screen items-center justify-center overflow-hidden", stickyClassName)}
          style={{ "--p": p.get() } as React.CSSProperties}
        >
          {background && <div className="absolute inset-0">{background}</div>}

          {/* Static or revealed content */}
          <div
            className={cn(reveal ? "absolute inset-0 z-10" : "z-10 text-center")}
            data-fly-content
            style={
              reveal
                ? {
                    // The mask draws the soft fade; the clip sits where the mask is already
                    // transparent, so it's never seen but keeps hidden controls unclickable.
                    maskImage: REVEAL_MASK,
                    WebkitMaskImage: REVEAL_MASK,
                    clipPath: `inset(0 calc(100% - ${EDGE}) 0 0)`,
                  }
                : undefined
            }
          >
            {children}
          </div>

          {hint && (
            <div ref={hintRef} className="pointer-events-none absolute inset-0 z-30" style={{ opacity: hintOpacity.get() }}>
              {hint}
            </div>
          )}

          {/* Animated image */}
          <div
            className={cn("pointer-events-none absolute top-0 z-20 flex h-full items-center", imageClassName)}
            style={{ left: IMAGE_LEFT, width: W }}
          >
            <img
              src={imageUrl}
              alt={imageAlt}
              className="h-auto w-full max-w-none select-none"
              draggable={false}
              onError={(e) => {
                // A missing image should leave the stage clean rather than show a stand-in.
                e.currentTarget.style.display = "none";
              }}
            />
          </div>
        </div>
      </div>
    );
  },
);

ScrollFlyIn.displayName = "ScrollFlyIn";

export { ScrollFlyIn };
