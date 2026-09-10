import React, { useRef, useEffect, useState } from 'react';
import { Button } from 'antd';
import { ClearOutlined, DeleteOutlined } from '@ant-design/icons';
import './SignatureCanvas.less';

const SignatureCanvas = ({ onSave, onClear }) => {
  const canvasRef = useRef(null);
  const isDrawingRef = useRef(false);
  const [hasSignature, setHasSignature] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();

    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    ctx.scale(2, 2);

    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, []);

  const getPosition = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  };

  const startDrawing = (e) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const pos = getPosition(e);

    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
    isDrawingRef.current = true;
    setHasSignature(true);
  };

  const draw = (e) => {
    if (!isDrawingRef.current) return;
    e.preventDefault();

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();

    // PointerEvent.getCoalescedEvents() 返回两次事件间的所有中间点，
    // 合并为一次 stroke() 绘制，避免触屏逐点绘制造成的延迟
    const coalesced = e.getCoalescedEvents?.();
    if (coalesced && coalesced.length > 0) {
      for (const pt of coalesced) {
        ctx.lineTo(pt.clientX - rect.left, pt.clientY - rect.top);
      }
      ctx.stroke();
    } else {
      const pos = getPosition(e);
      ctx.lineTo(pos.x, pos.y);
      ctx.stroke();
    }
  };

  const stopDrawing = () => {
    if (isDrawingRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      ctx.closePath();
      isDrawingRef.current = false;
    }
  };

  const handleSave = () => {
    const canvas = canvasRef.current;
    if (canvas && hasSignature) {
      const dataUrl = canvas.toDataURL('image/png');
      onSave?.(dataUrl);
    }
  };

  const handleClear = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();

    ctx.clearRect(0, 0, rect.width, rect.height);
    setHasSignature(false);
    onClear?.();
  };

  return (
    <div className="signature-canvas">
      <canvas
        ref={canvasRef}
        className="canvas-area"
        onPointerDown={startDrawing}
        onPointerMove={draw}
        onPointerUp={stopDrawing}
        onPointerLeave={stopDrawing}
      />
      <div className="canvas-actions">
        <Button
          icon={<DeleteOutlined />}
          onClick={handleClear}
          disabled={!hasSignature}
        >
          清空
        </Button>
        <Button
          type="primary"
          icon={<ClearOutlined />}
          onClick={handleSave}
          disabled={!hasSignature}
        >
          确认签字
        </Button>
      </div>
    </div>
  );
};

export default SignatureCanvas;