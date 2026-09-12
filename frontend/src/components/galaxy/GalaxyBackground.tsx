import React, { useEffect, useRef } from 'react';

interface Star {
  x: number;
  y: number;
  size: number;
  alpha: number;
  baseAlpha: number;
  twinkleSpeed: number;
}

export const GalaxyBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      initStars();
    };

    window.addEventListener('resize', handleResize);

    const STAR_COUNT = Math.min(120, Math.floor((width * height) / 10000));
    let stars: Star[] = [];

    const initStars = () => {
      stars = [];
      for (let i = 0; i < STAR_COUNT; i++) {
        const baseAlpha = Math.random() * 0.7 + 0.15;
        stars.push({
          x: Math.random() * width,
          y: Math.random() * height,
          size: Math.random() * 1.5 + 0.5,
          alpha: baseAlpha,
          baseAlpha,
          twinkleSpeed: (Math.random() * 0.02 + 0.005) * (Math.random() > 0.5 ? 1 : -1),
        });
      }
    };

    initStars();

    let frame = 0;
    const render = () => {
      frame++;
      ctx.clearRect(0, 0, width, height);

      // Deep space subtle gradient
      const grad = ctx.createRadialGradient(
        width * 0.7,
        height * 0.3,
        100,
        width * 0.5,
        height * 0.5,
        Math.max(width, height)
      );
      grad.addColorStop(0, 'rgba(139, 92, 246, 0.04)'); // Subtle violet
      grad.addColorStop(0.5, 'rgba(6, 182, 212, 0.02)'); // Subtle cyan
      grad.addColorStop(1, 'rgba(4, 4, 7, 1)'); // Space black
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, width, height);

      // Render stars
      for (let i = 0; i < stars.length; i++) {
        const s = stars[i];
        s.alpha += s.twinkleSpeed;
        if (s.alpha > 0.9 || s.alpha < 0.1) {
          s.twinkleSpeed = -s.twinkleSpeed;
        }

        // Slight celestial drift
        s.y -= 0.05;
        if (s.y < 0) s.y = height;

        ctx.fillStyle = `rgba(240, 245, 255, ${s.alpha.toFixed(2)})`;
        ctx.fillRect(s.x, s.y, s.size, s.size);
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 opacity-70"
    />
  );
};
