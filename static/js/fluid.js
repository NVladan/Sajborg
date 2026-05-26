(function () {
  var canvas = document.getElementById('hero-fluid-canvas');
  if (!canvas) return;

  var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
  if (!gl) return;

  function resize() {
    var rect = canvas.parentElement.getBoundingClientRect();
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(rect.width * dpr);
    canvas.height = Math.floor(rect.height * dpr);
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    gl.viewport(0, 0, canvas.width, canvas.height);
  }

  var vertSrc = 'attribute vec2 a_position;void main(){gl_Position=vec4(a_position,0.0,1.0);}';

  var fragSrc = [
    'precision highp float;',
    'uniform float u_time;',
    'uniform vec2 u_resolution;',
    '',
    'const vec3 COL_BLUE  = vec3(0.29, 0.565, 0.886);',
    'const vec3 COL_TEAL  = vec3(0.427, 0.835, 0.69);',
    'const vec3 COL_SKY   = vec3(0.357, 0.639, 0.851);',
    'const vec3 BG_DARK   = vec3(0.102, 0.082, 0.18);',
    'const vec3 BG_MID    = vec3(0.086, 0.129, 0.243);',
    '',
    'float hash(vec2 p) {',
    '  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);',
    '}',
    '',
    // Smooth trace line
    'float traceLine(float x, float width) {',
    '  return smoothstep(width, width * 0.3, abs(x));',
    '}',
    '',
    'void main() {',
    '  vec2 uv = gl_FragCoord.xy / u_resolution;',
    '  float aspect = u_resolution.x / u_resolution.y;',
    '  float t = u_time;',
    '',
    // Dark gradient background
    '  vec3 col = mix(BG_DARK, BG_MID, uv.y * 0.6 + uv.x * 0.2);',
    '',
    // --- CIRCUIT GRID ---
    '  float scale = 12.0;',
    '  vec2 gp = uv * vec2(scale * aspect, scale);',
    '  vec2 cellId = floor(gp);',
    '  vec2 cellUv = fract(gp) - 0.5;',
    '',
    // Horizontal traces - select ~40% of rows
    '  float hOn = step(0.58, hash(vec2(0.0, cellId.y + 0.5)));',
    '  float hTrace = traceLine(cellUv.y, 0.03) * hOn;',
    '',
    // Vertical traces - select ~40% of columns
    '  float vOn = step(0.58, hash(vec2(cellId.x + 0.5, 100.0)));',
    '  float vTrace = traceLine(cellUv.x, 0.03) * vOn;',
    '',
    // Combine traces with a subtle color
    '  float traceVal = max(hTrace, vTrace);',
    '  col += COL_BLUE * traceVal * 0.15;',
    '',
    // --- JUNCTION NODES at intersections ---
    '  float junc = hOn * vOn;',
    '  float nodeDist = length(cellUv);',
    '  float node = smoothstep(0.12, 0.04, nodeDist) * junc;',
    '  float nodePulse = 0.7 + 0.3 * sin(t * 1.5 + hash(cellId) * 6.28);',
    '  col += COL_TEAL * node * 0.35 * nodePulse;',
    '',
    // Node bright center
    '  float nodeCore = smoothstep(0.06, 0.01, nodeDist) * junc;',
    '  col += vec3(1.0) * nodeCore * 0.2 * nodePulse;',
    '',
    // --- GLOWING DATA PULSES traveling along traces ---
    '  for (float i = 0.0; i < 8.0; i++) {',
    '    float rowOrCol = hash(vec2(i, 200.0));',
    '    float speed = 0.3 + hash(vec2(i, 210.0)) * 0.4;',
    '    float pos = fract(t * speed * 0.1 + hash(vec2(i, 220.0)));',
    '    float isHoriz = step(0.5, hash(vec2(i, 230.0)));',
    '',
    '    vec2 pulseUv;',
    '    float onTrace;',
    '    if (isHoriz > 0.5) {',
    '      float row = floor(rowOrCol * scale);',
    '      float rowCheck = step(0.58, hash(vec2(0.0, row + 0.5)));',
    '      pulseUv = vec2(pos * scale * aspect - gp.x, (row + 0.5) / scale - uv.y) * vec2(1.0, scale);',
    '      onTrace = rowCheck;',
    '    } else {',
    '      float column = floor(rowOrCol * scale * aspect);',
    '      float colCheck = step(0.58, hash(vec2(column + 0.5, 100.0)));',
    '      pulseUv = vec2((column + 0.5) / (scale * aspect) - uv.x, pos * scale - gp.y) * vec2(scale * aspect, 1.0);',
    '      onTrace = colCheck;',
    '    }',
    '',
    '    float pulseDist = length(pulseUv);',
    '    float pulseGlow = 0.04 / (pulseDist + 0.01) * onTrace;',
    '',
    // Trail effect
    '    float trailAxis = isHoriz > 0.5 ? pulseUv.x : pulseUv.y;',
    '    float trailCross = isHoriz > 0.5 ? abs(pulseUv.y) : abs(pulseUv.x);',
    '    float trail = smoothstep(0.0, -0.5, trailAxis) * smoothstep(0.5, 0.0, -trailAxis);',
    '    trail *= smoothstep(0.08, 0.0, trailCross) * onTrace;',
    '',
    '    vec3 pCol = mod(i, 2.0) < 1.0 ? COL_TEAL : COL_BLUE;',
    '    col += pCol * pulseGlow * 0.15;',
    '    col += pCol * trail * 0.12;',
    '  }',
    '',
    // --- COMPONENT CHIPS ---
    '  for (float i = 0.0; i < 5.0; i++) {',
    '    vec2 chipCenter = vec2(',
    '      (hash(vec2(i, 300.0)) * 0.7 + 0.15) * aspect,',
    '      hash(vec2(i, 310.0)) * 0.6 + 0.2',
    '    );',
    '    vec2 chipSize = vec2(',
    '      0.02 + hash(vec2(i, 320.0)) * 0.015,',
    '      0.03 + hash(vec2(i, 330.0)) * 0.025',
    '    );',
    '    vec2 cp = uv * vec2(aspect, 1.0) - chipCenter;',
    '    vec2 d = abs(cp) - chipSize;',
    '    float bd = length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);',
    '',
    '    float chipPulse = 0.6 + 0.4 * sin(t * 1.2 + i * 2.1);',
    '',
    // Outline
    '    float outline = smoothstep(0.004, 0.001, abs(bd));',
    '    col += COL_SKY * outline * 0.4 * chipPulse;',
    '',
    // Fill
    '    float fill = smoothstep(0.002, -0.002, bd);',
    '    col += COL_BLUE * fill * 0.06 * chipPulse;',
    '',
    // Pin lines on sides
    '    float pins = 0.0;',
    '    if (abs(cp.x) > chipSize.x - 0.002 && abs(cp.y) < chipSize.y + 0.015) {',
    '      float pinPattern = smoothstep(0.3, 0.5, fract(cp.y * 40.0));',
    '      pins = pinPattern * smoothstep(chipSize.x + 0.015, chipSize.x, abs(cp.x));',
    '    }',
    '    col += COL_SKY * pins * 0.15 * chipPulse;',
    '  }',
    '',
    // Subtle vignette
    '  vec2 vc = uv - 0.5;',
    '  col *= 1.0 - 0.25 * dot(vc * vec2(1.4, 2.0), vc * vec2(1.4, 2.0));',
    '',
    '  gl_FragColor = vec4(col, 1.0);',
    '}'
  ].join('\n');

  function compile(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.warn('Shader error:', gl.getShaderInfoLog(s));
      return null;
    }
    return s;
  }

  var vs = compile(gl.VERTEX_SHADER, vertSrc);
  var fs = compile(gl.FRAGMENT_SHADER, fragSrc);
  if (!vs || !fs) return;

  var prog = gl.createProgram();
  gl.attachShader(prog, vs);
  gl.attachShader(prog, fs);
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return;

  gl.useProgram(prog);

  var buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
    -1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1
  ]), gl.STATIC_DRAW);

  var aPos = gl.getAttribLocation(prog, 'a_position');
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

  var uTime = gl.getUniformLocation(prog, 'u_time');
  var uRes = gl.getUniformLocation(prog, 'u_resolution');

  resize();
  window.addEventListener('resize', resize);

  var start = performance.now();
  var last = 0;

  function frame(now) {
    if (now - last < 33) { requestAnimationFrame(frame); return; }
    last = now;
    gl.uniform1f(uTime, (now - start) * 0.001);
    gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
