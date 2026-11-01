/* Canvas host for the site's bounded #ui/draw subset. No HTML or JS from Xu. */
(function (root) {
  'use strict';
  var WIDTH = 640, HEIGHT = 360, MAX_EVENTS = 100000;
  // XUUI 0.1.0 font-sans; the preview can also supply the pinned CSS token.
  var fontStack = '"Avenir Next", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif';
  // Argument types: number, color, text. Validate before touching a canvas.
  var signatures = {
    begin: '', present: '', cancel: '', push: '', pop: '', origin: '',
    bgcolor: 'c', color: 'c', fill: 'c', stroke: 'c', width: 'n',
    translate: 'nn', rotate: 'n', scale: 'nn', clip_rect: 'nnnn',
    fill_rect: 'nnnnc', stroke_rect: 'nnnncn', round_rect: 'nnnnnccn',
    path_begin: '', path_move: 'nn', path_line: 'nn', path_cubic: 'nnnnnn', path_close: '', path_fill: 'c', path_stroke: 'cn',
    layout_text: 'nnncnt', line: 'nnnncn', text: 'nnnct', rect: 'nnnn', circle: 'nnn',
  };
  function frame(commands) {
    if (typeof commands !== 'string' || commands.length > 262144) throw Error('Invalid UI command buffer');
    var lines = commands.split('\n');
    if (lines.at(-1) === '') lines.pop();
    if (lines.length > 4096) throw Error('UI command count limit exceeded');
    var pending = null, committed = null, depth = 0, pathActive = false;
    lines.forEach(function (line) {
      var parts = line.split('\t'), op = parts.shift(), signature = signatures[op];
      // circle has a pen form and an explicit fill/stroke form, like the SDK.
      if (op === 'circle' && parts.length === 6) signature = 'nnnccn';
      if (op === 'path_stroke' && parts.length === 5) signature = 'cnnnn';
      if (typeof signature !== 'string' || parts.length !== signature.length) throw Error('Unsupported UI command: ' + op);
      var args = parts.map(function (value, index) {
        var type = signature[index];
        if (type === 'c') {
          if (value !== '-' && !/^#[0-9a-f]{6}([0-9a-f]{2})?$/i.test(value)) throw Error('Invalid UI color');
        } else if (type === 'n') {
          if (!/^-?\d+(?:\.\d+)?$/.test(value) || Math.abs(Number(value)) > 100000) throw Error('Invalid UI coordinate');
          return Number(value);
        } else if (value.length > 4096) throw Error('UI text limit exceeded');
        return value;
      });
      if (op === 'begin') { pending = []; depth = 0; pathActive = false; return; }
      if (op === 'cancel') { pending = null; depth = 0; pathActive = false; return; }
      if (op === 'present') {
        if (!pending) throw Error('UI present requires begin');
        committed = pending; pending = null; depth = 0; pathActive = false; return;
      }
      if (!pending) throw Error('UI drawing requires begin');
      if (op === 'path_begin') pathActive = true;
      else if (op.startsWith('path_')) {
        if (!pathActive) throw Error('UI path command requires path_begin');
        if ((op === 'path_fill' || op === 'path_stroke')) pathActive = false;
      }
      if (op === 'layout_text' && args[4] < 0) throw Error('Negative UI text width');
      if (op === 'push' && ++depth > 32) throw Error('UI transform stack limit exceeded');
      if (op === 'pop' && --depth < 0) throw Error('Unbalanced UI pop');
      if (['rect', 'fill_rect', 'stroke_rect', 'round_rect', 'clip_rect'].includes(op) && (args[2] < 0 || args[3] < 0)) throw Error('Negative UI size');
      if (op === 'circle' && args[2] < 0 || op === 'round_rect' && args[4] < 0) throw Error('Negative UI radius');
      if ((op === 'text' || op === 'layout_text') && (args[2] < 1 || args[2] > 256)) throw Error('Invalid UI font size');
      var strokeWidth = op === 'path_stroke' ? args[1] : args.at(-1);
      if (['path_stroke', 'width', 'stroke_rect', 'round_rect', 'line'].includes(op) && (strokeWidth < 1 || strokeWidth > 1000) || op === 'circle' && args.length === 6 && (args[5] < 1 || args[5] > 1000)) throw Error('Invalid UI stroke width');
      if (op === 'path_stroke' && args.length === 5 &&
          (!Number.isInteger(args[2]) || args[2] < 0 || args[2] > 2 || !Number.isInteger(args[3]) || args[3] < 0 || args[3] > 2 || args[4] <= 0 || args[4] > 1000)) throw Error('Invalid UI stroke options');
      pending.push({op: op, args: args});
    });
    return committed;
  }
  function render(canvas, commands) {
    var display = frame(commands);
    return draw(canvas, display);
  }
  // Kept separate so the benchmark can time validation and Canvas calls.
  function draw(canvas, display) {
    if (!display) return false; // cancel or an unfinished frame never commits.
    var ratio = Number(canvas.ownerDocument.defaultView?.devicePixelRatio) || 1;
    ratio = Math.max(1, Math.min(3, ratio));
    var staging = canvas.ownerDocument.createElement('canvas');
    staging.width = Math.round(WIDTH * ratio); staging.height = Math.round(HEIGHT * ratio);
    var ctx = staging.getContext('2d');
    if (!ctx) throw Error('Canvas 2D is unavailable');
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    function origin() { ctx.setTransform(ratio, 0, 0, ratio, 0, 0); }
    origin();
    var pen = {fill: '#000000', stroke: '-', width: 1}, stack = [];
    var computed = canvas.ownerDocument.defaultView?.getComputedStyle?.(canvas);
    var family = computed?.getPropertyValue('--xu-font-sans').trim() || fontStack;
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, WIDTH, HEIGHT);
    function paint(fill, stroke, width) {
      if (fill !== '-') { ctx.fillStyle = fill; ctx.fill(); }
      if (stroke !== '-') { ctx.strokeStyle = stroke; ctx.lineWidth = width; ctx.stroke(); }
    }
    display.forEach(function (command) {
      var a = command.args, op = command.op;
      if (op === 'bgcolor') {
        ctx.save(); origin(); ctx.fillStyle = a[0] === '-' ? '#ffffff' : a[0]; ctx.fillRect(0, 0, WIDTH, HEIGHT); ctx.restore();
      } else if (op === 'color') { pen.fill = a[0]; pen.stroke = a[0]; }
      else if (op === 'fill') pen.fill = a[0];
      else if (op === 'stroke') pen.stroke = a[0];
      else if (op === 'width') pen.width = a[0];
      else if (op === 'push') { ctx.save(); stack.push({...pen}); }
      else if (op === 'pop') { ctx.restore(); pen = stack.pop(); }
      else if (op === 'origin') origin();
      else if (op === 'translate') ctx.translate(a[0], a[1]);
      else if (op === 'rotate') ctx.rotate(a[0] * Math.PI / 180);
      else if (op === 'scale') ctx.scale(a[0] / 100, a[1] / 100);
      else if (op === 'clip_rect') { ctx.beginPath(); ctx.rect(...a); ctx.clip(); }
      else if (op === 'path_begin') ctx.beginPath();
      else if (op === 'path_move') ctx.moveTo(...a);
      else if (op === 'path_line') ctx.lineTo(...a);
      else if (op === 'path_cubic') ctx.bezierCurveTo(...a);
      else if (op === 'path_close') ctx.closePath();
      else if (op === 'path_fill') paint(a[0], '-', 1);
      else if (op === 'path_stroke') {
        ctx.save();
        ctx.lineCap = ['butt','round','square'][a[2] || 0];
        ctx.lineJoin = ['miter','round','bevel'][a[3] || 0];
        ctx.miterLimit = a[4] || 10;
        paint('-', a[0], a[1]); ctx.restore();
      }
      else if (op === 'layout_text') {
        if (a[3] !== '-' && a[4] > 0 && a[5]) {
          ctx.save();
          ctx.font = a[2] + 'px ' + family;
          ctx.textBaseline = 'top';
          ctx.fillStyle = a[3];
          // Xu's bounded layout supplies the origin and estimated advance.
          // Preserve the font's natural glyph proportions at that origin;
          // enclosing draw clips still control overflow for text fields.
          ctx.fillText(a[5], a[0], a[1]); ctx.restore();
        }
      } else if (op === 'text') {
        if (a[3] !== '-') { ctx.font = a[2] + 'px ' + family; ctx.textBaseline = 'top'; ctx.fillStyle = a[3]; ctx.fillText(a[4], a[0], a[1]); }
      } else if (op === 'line') {
        ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(a[2], a[3]); paint('-', a[4], a[5]);
      } else {
        ctx.beginPath();
        var fill = pen.fill, stroke = pen.stroke, width = pen.width;
        if (op === 'circle') {
          ctx.arc(a[0], a[1], a[2], 0, 2 * Math.PI);
          if (a.length === 6) { fill = a[3]; stroke = a[4]; width = a[5]; }
        } else if (op === 'round_rect') {
          if (typeof ctx.roundRect === 'function') {
            ctx.roundRect(a[0], a[1], a[2], a[3], a[4]);
          } else {
            var rx = a[0], ry = a[1], rw = a[2], rh = a[3], r = Math.min(a[4], Math.min(rw / 2, rh / 2));
            ctx.moveTo(rx + r, ry);
            ctx.arcTo(rx + rw, ry, rx + rw, ry + rh, r);
            ctx.arcTo(rx + rw, ry + rh, rx, ry + rh, r);
            ctx.arcTo(rx, ry + rh, rx, ry, r);
            ctx.arcTo(rx, ry, rx + rw, ry, r);
            ctx.closePath();
          }
          fill = a[5]; stroke = a[6]; width = a[7];
        } else {
          ctx.rect(a[0], a[1], a[2], a[3]);
          if (op === 'fill_rect') { fill = a[4]; stroke = '-'; }
          if (op === 'stroke_rect') { fill = '-'; stroke = a[4]; width = a[5]; }
        }
        paint(fill, stroke, width);
      }
    });
    // Only the complete, validated last present reaches the visible canvas.
    var target = canvas.getContext('2d');
    if (!target) throw Error('Canvas 2D is unavailable');
    canvas.width = staging.width; canvas.height = staging.height;
    target.imageSmoothingEnabled = true;
    target.imageSmoothingQuality = 'high';
    target.drawImage(staging, 0, 0);
    return true;
  }
  function measureText(text, size, font) {
    if (typeof document === 'undefined') return {width: (text ? text.length : 0) * (size || 14) * 0.6};
    var measureCanvas = document.createElement('canvas');
    var ctx = measureCanvas.getContext('2d');
    if (!ctx) return {width: (text ? text.length : 0) * (size || 14) * 0.6};
    ctx.font = (size || 14) + 'px ' + (font || fontStack);
    return ctx.measureText(text || '');
  }
  root.XuPlayCanvas = {render: render, frame: frame, draw: draw, measureText: measureText, fontStack: fontStack, width: WIDTH, height: HEIGHT, maxEvents: MAX_EVENTS};
})(typeof window === 'undefined' ? globalThis : window);
