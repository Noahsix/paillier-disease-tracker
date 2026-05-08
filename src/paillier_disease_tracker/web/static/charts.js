(function () {
  function setupCanvas(canvas) {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, width: rect.width, height: rect.height };
  }

  function renderLineChart(canvas, labels, series, options) {
    const { ctx, width, height } = setupCanvas(canvas);
    ctx.clearRect(0, 0, width, height);

    const padding = { top: 20, right: 24, bottom: 32, left: 46 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const maxValue = Math.max(1, ...series.flatMap(item => item.values));
    const xStep = labels.length > 1 ? chartWidth / (labels.length - 1) : chartWidth;

    ctx.strokeStyle = "rgba(15, 23, 42, 0.2)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, padding.top + chartHeight);
    ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
    ctx.stroke();

    ctx.fillStyle = "#5b6472";
    ctx.font = "12px Trebuchet MS";
    labels.forEach((label, index) => {
      const x = padding.left + xStep * index;
      ctx.fillText(String(label), x - 8, padding.top + chartHeight + 20);
    });

    series.forEach(item => {
      ctx.strokeStyle = item.color;
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      item.values.forEach((value, index) => {
        const x = padding.left + xStep * index;
        const y = padding.top + chartHeight - (value / maxValue) * chartHeight;
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      ctx.fillStyle = item.color;
      item.values.forEach((value, index) => {
        const x = padding.left + xStep * index;
        const y = padding.top + chartHeight - (value / maxValue) * chartHeight;
        ctx.beginPath();
        ctx.arc(x, y, 3.5, 0, Math.PI * 2);
        ctx.fill();
      });
    });

    if (options && options.title) {
      ctx.fillStyle = "#10131a";
      ctx.font = "14px Georgia";
      ctx.fillText(options.title, padding.left, 14);
    }
  }

  function renderLegend(container, series) {
    container.innerHTML = "";
    series.forEach(item => {
      const chip = document.createElement("span");
      const dot = document.createElement("i");
      dot.style.background = item.color;
      chip.appendChild(dot);
      chip.appendChild(document.createTextNode(item.label));
      container.appendChild(chip);
    });
  }

  window.ChartKit = {
    renderLineChart,
    renderLegend,
  };
})();
