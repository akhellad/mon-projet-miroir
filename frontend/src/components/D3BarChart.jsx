// frontend/src/components/D3BarChart.jsx
import React, { useEffect, useRef, memo } from 'react';
import * as d3 from 'd3';
import './Dashboard.css';

const D3BarChart = memo(function D3BarChart({
  data,
  xField, // Field name for X-axis categories (e.g., 'name')
  yField, // Field name for Y-axis values (e.g., 'population' or 'communes')
  xAxisLabel = '', // Optional label for X axis
  yAxisLabel = '', // Optional label for Y axis
  tooltipFormat = (d) => `${d[xField]}: ${d[yField]?.toLocaleString('fr-FR')}`, // Tooltip content function
  color = "#3b82f6", // Default bar color
  width = 600, // Default width
  height = 350, // Default height
  rotateXLabels = false, // Rotate X labels if they might overlap
}) {
  const svgRef = useRef();
  const tooltipRef = useRef();

  useEffect(() => {
    if (!data || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous render

    // --- Setup Dimensions & Margins ---
    const margin = { top: 20, right: 30, bottom: rotateXLabels ? 100 : 60, left: 70 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    svg.attr('viewBox', `0 0 ${width} ${height}`) // Make it responsive
       .attr('preserveAspectRatio', 'xMidYMid meet')
       .style('max-width', '100%')
       .style('height', 'auto');

    const chartGroup = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // --- Scales ---
    const xScale = d3.scaleBand()
      .domain(data.map(d => d[xField]))
      .range([0, innerWidth])
      .padding(0.2); // Adjust padding between bars

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(data, d => d[yField]) * 1.05]).nice() // Add 5% padding top
      .range([innerHeight, 0]);

    // --- Axes ---
    const xAxis = d3.axisBottom(xScale).tickSizeOuter(0);
    const xAxisGroup = chartGroup.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(xAxis)
      .attr("class", "x-axis"); // Add class for styling

    if (rotateXLabels) {
        xAxisGroup.selectAll("text")
            .attr("transform", "rotate(-45)")
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", ".15em");
    }

    const yAxis = d3.axisLeft(yScale)
                    .ticks(5)
                    .tickFormat(d3.format(",.0f"))
                    .tickSize(-innerWidth);
    const yAxisGroup = chartGroup.append("g")
      .call(yAxis)
      .attr("class", "y-axis"); // Add class for styling

    yAxisGroup.select(".domain").remove(); // Remove y-axis line
    // yAxisGroup.selectAll(".tick line")
    //           .attr("stroke", "#e5e7eb") // Lighter grid lines
    //           .attr("stroke-dasharray", "2,2"); // Dashed grid lines
    // yAxisGroup.append("text") // Y Axis Label
    //   .attr("class", "axis-label")
    //   .attr("transform", "rotate(-90)")
    //   .attr("y", -margin.left + 20)
    //   .attr("x", -innerHeight / 2)
    //   .style("text-anchor", "middle")
    //   .text(yAxisLabel);


    // --- Tooltip Setup ---
    const tooltip = d3.select(tooltipRef.current);

    const handleMouseOver = (event, d) => {
      tooltip.style('opacity', 1)
             .html(tooltipFormat(d)); // Use the formatting function
    };

    const handleMouseMove = (event) => {
      // Position tooltip relative to the SVG container
      const [x, y] = d3.pointer(event, svg.node());
      tooltip.style('left', `${x + 15}px`) // Offset slightly
             .style('top', `${y}px`);
    };

    const handleMouseLeave = () => {
      tooltip.style('opacity', 0);
    };

    // --- Bars with Transitions & Tooltips ---
    chartGroup.selectAll(".bar")
      .data(data)
      .join("rect")
        .attr("class", "bar")
        .attr("fill", color)
        .attr("x", d => xScale(d[xField]))
        .attr("width", xScale.bandwidth())
        .attr("rx", 4) // Rounded corners
        .attr("ry", 4)
        // Initial state for transition
        .attr("y", d => yScale(0))
        .attr("height", 0)
        // Tooltip events
        .on('mouseover', handleMouseOver)
        .on('mousemove', handleMouseMove)
        .on('mouseleave', handleMouseLeave)
        // Transition
        .transition()
        .duration(1000) // Animation duration
        .ease(d3.easeCubicOut) // Easing function
        .delay((d, i) => i * 60) // Stagger the animation
        .attr("y", d => yScale(d[yField]))
        .attr("height", d => innerHeight - yScale(d[yField]));

    // --- Add X Axis Label ---
     chartGroup.append("text")
      .attr("class", "axis-label")
      .attr("x", innerWidth / 2)
      .attr("y", innerHeight + margin.bottom - 10) // Adjust position
      .style("text-anchor", "middle")
      .text(xAxisLabel);


  }, [data, xField, yField, xAxisLabel, yAxisLabel, tooltipFormat, color, width, height, rotateXLabels]); // Re-run effect if any prop changes

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: `${width}px`, margin: 'auto' }}>
      <svg ref={svgRef}></svg>
      {/* Tooltip element (initially hidden) */}
      <div ref={tooltipRef} className="d3-tooltip" style={{ opacity: 0 }}></div>
    </div>
  );
});

export default D3BarChart;