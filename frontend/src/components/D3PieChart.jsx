// frontend/src/components/D3PieChart.jsx
import React, { useEffect, useRef, memo } from 'react';
import * as d3 from 'd3';
import './Dashboard.css';

const D3PieChart = memo(function D3PieChart({
  data,
  valueField, // Field name for values (e.g., 'communes')
  nameField,  // Field name for labels (e.g., 'name')
  colors = ['#1e3a8a', '#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe'], // Default colors
  width = 400,
  height = 300,
  innerRadiusFactor = 0, // 0 for Pie, > 0 for Donut
  labelThreshold = 0.05, // Only show labels for slices > 5%
}) {
  const svgRef = useRef();
  const tooltipRef = useRef();

  useEffect(() => {
    if (!data || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous render

    const radius = Math.min(width, height) / 2;
    const innerRadius = radius * innerRadiusFactor;

    svg.attr('viewBox', `${-width / 2} ${-height / 2} ${width} ${height}`)
       .attr('preserveAspectRatio', 'xMidYMid meet')
       .style('max-width', '100%')
       .style('height', 'auto');

    // Color scale
    const colorScale = d3.scaleOrdinal()
      .domain(data.map(d => d[nameField]))
      .range(colors);

    // Pie generator
    const pie = d3.pie()
      .value(d => d[valueField])
      .sort(null); // Keep original data order

    // Arc generator
    const arc = d3.arc()
      .innerRadius(innerRadius)
      .outerRadius(radius * 0.8); // Leave space for labels/tooltips

    const arcs = pie(data);

    // Tooltip Setup
    const tooltip = d3.select(tooltipRef.current);
    const total = d3.sum(data, d => d[valueField]);

    const handleMouseOver = (event, d) => {
        const percent = ((d.data[valueField] / total) * 100).toFixed(1);
        tooltip.style('opacity', 1)
               .html(`${d.data[nameField]}<br/>${d.data[valueField]?.toLocaleString('fr-FR')} (${percent}%)`);
    };

    const handleMouseMove = (event) => {
        // Position relative to the container div
        const container = svgRef.current.parentNode;
        const [x, y] = d3.pointer(event, container);
        tooltip.style('left', `${x + 15}px`)
               .style('top', `${y}px`);
    };

    const handleMouseLeave = () => {
        tooltip.style('opacity', 0);
    };

    // Draw slices with transitions
    const path = svg.selectAll("path")
      .data(arcs)
      .join("path")
        .attr("class", "slice")
        .attr("fill", d => colorScale(d.data[nameField]))
        .attr("stroke", "white")
        .style("stroke-width", "3px")
        .on('mouseover', handleMouseOver)
        .on('mousemove', handleMouseMove)
        .on('mouseleave', handleMouseLeave)
        // Transition
        .transition()
        .duration(1200)
        .ease(d3.easeCubicOut)
        .attrTween("d", function(d) {
            const interpolate = d3.interpolate({ startAngle: 0, endAngle: 0 }, d);
            return function(t) {
                return arc(interpolate(t));
            };
        });

    // Optional: Add labels directly on slices (can get crowded)
    const labelArc = d3.arc()
        .innerRadius(radius * 0.9)
        .outerRadius(radius * 0.9);

    svg.selectAll('text.label')
        .data(arcs)
        .enter()
        .append('text')
        .attr('class', 'label')
        .attr('transform', d => `translate(${labelArc.centroid(d)})`)
        .attr('dy', '0.35em')
        .style('text-anchor', 'middle')
        .style('font-size', '10px')
        .style('fill', '#333')
        .text(d => {
            const percent = d.data[valueField] / total;
            return percent >= labelThreshold ? `${(percent * 100).toFixed(0)}%` : ''; // Show % if above threshold
        });


  }, [data, valueField, nameField, colors, width, height, innerRadiusFactor, labelThreshold]);

  return (
     <div style={{ position: 'relative', width: '100%', maxWidth: `${width}px`, margin: 'auto' }}>
      <svg ref={svgRef}></svg>
      {/* Tooltip element */}
      <div ref={tooltipRef} className="d3-tooltip" style={{ opacity: 0 }}></div>
    </div>
  );
});

export default D3PieChart;