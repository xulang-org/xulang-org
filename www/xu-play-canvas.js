/* Canvas host for the site's bounded #ui/draw subset. No HTML or JS from Xu. */
(function (root) {
  'use strict';
  var WIDTH = 640, HEIGHT = 360, MAX_EVENTS = 100000;
  // The bounded browser TextLayout contract in stdlib/frame.xu is 1.25 em.
  var LAYOUT_LINE_HEIGHT = 1.25;
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
  function findSpinner(display) {
    var circles = [];
    for (var i = 0; i < display.length; i++) {
      var cmd = display[i];
      if (cmd.op === 'circle') {
        var prev = display[i - 1];
        var fillColor = (cmd.args.length === 6 ? cmd.args[3] : (prev && prev.op === 'fill' ? prev.args[0] : null));
        circles.push({x: cmd.args[0], y: cmd.args[1], r: cmd.args[2], fill: fillColor, index: i});
      }
    }
    if (circles.length < 8) return null;
    for (var j = 0; j <= circles.length - 8; j++) {
      var group = circles.slice(j, j + 8);
      var r = group[0].r;
      var sameR = group.every(function (c) { return Math.abs(c.r - r) < 0.01; });
      if (!sameR) continue;
      var cx = group.reduce(function (sum, c) { return sum + c.x; }, 0) / 8;
      var cy = group.reduce(function (sum, c) { return sum + c.y; }, 0) / 8;
      var dists = group.map(function (c) { return Math.hypot(c.x - cx, c.y - cy); });
      var avgDist = dists.reduce(function (sum, d) { return sum + d; }, 0) / 8;
      var isCircle = avgDist > 5 && dists.every(function (d) { return Math.abs(d - avgDist) < 1.0; });
      if (!isCircle) continue;
      var fills = group.map(function (c) { return c.fill; });
      var allSame = fills.every(function (f) { return f === fills[0]; });
      return {
        cx: cx, cy: cy, radius: avgDist, dotR: r,
        colors: fills, running: !allSame,
        firstIndex: group[0].index
      };
    }
    return null;
  }
  function render(canvas, commands) {
    var display = frame(commands);
    return draw(canvas, display);
  }
  // Kept separate so the benchmark can time validation and Canvas calls.
  function draw(canvas, display) {
    if (!display) return false; // cancel or an unfinished frame never commits.
    if (canvas && canvas.__xu_spinner_raf) {
      var caf = (canvas.ownerDocument?.defaultView?.cancelAnimationFrame) || (typeof cancelAnimationFrame === 'function' ? cancelAnimationFrame : null);
      if (caf) caf(canvas.__xu_spinner_raf);
      canvas.__xu_spinner_raf = null;
    }
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
    var monoFamily = computed?.getPropertyValue('--xu-font-mono').trim() || '"JetBrains Mono", "SFMono-Regular", Consolas, monospace';
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, WIDTH, HEIGHT);
    function paint(fill, stroke, width) {
      if (fill !== '-') { ctx.fillStyle = fill; ctx.fill(); }
      if (stroke !== '-') { ctx.strokeStyle = stroke; ctx.lineWidth = width; ctx.stroke(); }
    }
    var spin = findSpinner(display);
    var bgData = null, sx = 0, sy = 0;
    display.forEach(function (command, cmdIndex) {
      if (spin && spin.running && !bgData && cmdIndex === spin.firstIndex) {
        sx = Math.max(0, Math.floor((spin.cx - spin.radius - spin.dotR - 2) * ratio));
        sy = Math.max(0, Math.floor((spin.cy - spin.radius - spin.dotR - 2) * ratio));
        var sw = Math.ceil((spin.radius + spin.dotR + 2) * 2 * ratio);
        var sh = sw;
        try { bgData = ctx.getImageData(sx, sy, sw, sh); } catch (e) {}
      }
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
        var text = a[5], lineHeight = a[2] * LAYOUT_LINE_HEIGHT;
        if (a[3] !== '-' && a[4] > 0 && lineHeight > 0 && text) {
          ctx.save();
          var useMono = canvas.dataset?.font === 'mono' ||
                        (canvas.dataset?.example && /text-selection|input|text-area|field/.test(canvas.dataset.example)) ||
                        (typeof document !== 'undefined' && document.getElementById('xu-play-src')?.value && /ui-text-selection|measure_prefix|hit_col|TextSelection/.test(document.getElementById('xu-play-src').value));
          var textFont = useMono ? monoFamily : family;
          ctx.font = a[2] + 'px ' + textFont;
          ctx.textBaseline = 'alphabetic';
          ctx.fillStyle = a[3];
          var metrics = typeof ctx.measureText === 'function' ? ctx.measureText(text) : null;
          var ascent = metrics?.actualBoundingBoxAscent, descent = metrics?.actualBoundingBoxDescent;
          if (!Number.isFinite(ascent) || !Number.isFinite(descent) || ascent + descent <= 0) {
            ascent = metrics?.fontBoundingBoxAscent; descent = metrics?.fontBoundingBoxDescent;
          }
          if (!Number.isFinite(ascent) || !Number.isFinite(descent) || ascent + descent <= 0) {
            ascent = a[2] * 0.8; descent = a[2] * 0.2;
          }
          var y = a[1] + (lineHeight + ascent - descent) * 0.5;
          if (useMono) {
            var chars = Array.from(text);
            var cellWidth = a[2] * 0.6;
            for (var ci = 0; ci < chars.length; ci++) {
              ctx.fillText(chars[ci], a[0] + ci * cellWidth, y);
            }
          } else {
            ctx.fillText(text, a[0], y);
          }
          ctx.restore();
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
    var raf = (canvas.ownerDocument?.defaultView?.requestAnimationFrame) || (typeof requestAnimationFrame === 'function' ? requestAnimationFrame : null);
    if (spin && spin.running && bgData && raf) {
      var perf = (canvas.ownerDocument?.defaultView?.performance) || (typeof performance !== 'undefined' ? performance : null);
      var getTime = perf && perf.now ? perf.now.bind(perf) : Date.now;
      var t0 = getTime();
      function loop(now) {
        var elapsed = (typeof now === 'number' ? now : getTime()) - t0;
        var angle = ((elapsed % 900) / 900) * 2 * Math.PI;
        try { target.putImageData(bgData, sx, sy); } catch (e) {}
        target.save();
        target.setTransform(ratio, 0, 0, ratio, 0, 0);
        for (var k = 0; k < 8; k++) {
          var a = (k / 8.0) * 2 * Math.PI + angle;
          var x = spin.cx + Math.cos(a) * spin.radius;
          var y = spin.cy + Math.sin(a) * spin.radius;
          target.beginPath();
          target.arc(x, y, spin.dotR, 0, 2 * Math.PI);
          target.fillStyle = spin.colors[k];
          target.fill();
        }
        target.restore();
        canvas.__xu_spinner_raf = raf(loop);
      }
      canvas.__xu_spinner_raf = raf(loop);
    }
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
