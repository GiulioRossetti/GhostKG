// Ghost KG - Memory Heatmap Visualization

let rawData = null;
let simulation = null;
let currentStep = 0;
let currentAgent = "";
let isPlaying = false;
let playInterval = null;
let stepDelay = 1000;

const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("#graph").append("svg")
    .attr("width", width).attr("height", height)
    .call(d3.zoom().on("zoom", (e) => g.attr("transform", e.transform)))
    .on("dblclick.zoom", null);

svg.append("defs").selectAll("marker")
    .data(["end"]).enter().append("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10").attr("refX", 22).attr("refY", 0)
    .attr("markerWidth", 6).attr("markerHeight", 6).attr("orient", "auto")
    .append("path").attr("d", "M0,-5L10,0L0,5").attr("fill", "#555");

const g = svg.append("g");
const linkGroup = g.append("g").attr("class", "links");
const edgeLabelGroup = g.append("g").attr("class", "edge-labels");
const nodeGroup = g.append("g").attr("class", "nodes");
const labelGroup = g.append("g").attr("class", "node-labels");

// --- COLOR SCALES ---
const memoryScale = d3.scaleLinear()
    .domain([0.0, 0.2, 0.5, 1.0])
    .range(["#37474F", "#546E7A", "#FFEB3B", "#00E676"])
    .interpolate(d3.interpolateRgb);

// Load data from simulation_history.json
d3.json("simulation_history.json").then(data => {
    rawData = data;

    const select = d3.select("#agentSelect");

    // 1. Add "ALL AGENTS" Option
    select.append("option").text("ALL AGENTS (Consolidated)").attr("value", "ALL_AGENTS");

    data.agents.forEach(agent => {
        select.append("option").text(agent).attr("value", agent);
    });

    // Default to first real agent
    currentAgent = data.agents[0];
    select.property("value", currentAgent);

    d3.select("#timeSlider").attr("max", data.steps.length - 1);

    simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(d => d.id).distance(150))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide().radius(35));

    updateVisualization();

    select.on("change", function() { currentAgent = this.value; updateVisualization(); });
    d3.select("#timeSlider").on("input", function() {
        currentStep = parseInt(this.value);
        updateVisualization();
        if(isPlaying) stopPlay();
    });
    d3.select("#playBtn").on("click", togglePlay);
    d3.select("#speedSlider").on("input", function() {
        stepDelay = parseInt(this.value);
        if (isPlaying) { clearInterval(playInterval); playInterval = setInterval(nextStep, stepDelay); }
    });

}).catch(err => console.error(err));

function togglePlay() { isPlaying ? stopPlay() : startPlay(); }

function startPlay() {
    isPlaying = true;
    d3.select("#playBtn").text("❚❚ PAUSE").classed("playing", true);
    if (currentStep >= rawData.steps.length - 1) {
        currentStep = 0; d3.select("#timeSlider").property("value", 0); updateVisualization();
    }
    playInterval = setInterval(nextStep, stepDelay);
}

function stopPlay() {
    isPlaying = false; d3.select("#playBtn").text("▶ PLAY").classed("playing", false); clearInterval(playInterval);
}

function nextStep() {
    if (currentStep < rawData.steps.length - 1) {
        currentStep++; d3.select("#timeSlider").property("value", currentStep); updateVisualization();
    } else stopPlay();
}

function updateVisualization() {
    const stepData = rawData.steps[currentStep];

    d3.select("#stepDisplay").text(currentStep);
    d3.select("#roundDisplay").text(`Round ${stepData.round}`);
    d3.select("#actionDisplay").text(stepData.action);

    let rawNodes = [];
    let rawLinks = [];

    // --- DATA GATHERING STRATEGY ---
    if (currentAgent === "ALL_AGENTS") {
        // MERGE & FILTER MODE
        const mergedLinksMap = new Map();
        const connectedNodeIds = new Set();
        const mergedNodesMap = new Map();

        // 1. Collect all valid links from all agents (excluding "I")
        Object.values(stepData.graphs).forEach(agentGraph => {
            agentGraph.links.forEach(link => {
                // FILTER: Do not show edges connected to "I"
                if (link.source !== "I" && link.target !== "I") {
                    // Deduplicate based on content
                    const key = `${link.source}-${link.target}-${link.label}`;
                    if (!mergedLinksMap.has(key)) {
                        mergedLinksMap.set(key, { ...link }); // Copy to allow D3 mutation
                        connectedNodeIds.add(link.source);
                        connectedNodeIds.add(link.target);
                    }
                }
            });
        });

        // 2. Collect only the nodes involved in valid links
        Object.values(stepData.graphs).forEach(agentGraph => {
            agentGraph.nodes.forEach(node => {
                // FILTER: Only keep nodes that have a valid connection
                if (connectedNodeIds.has(node.id)) {
                    // Deduplicate nodes by ID
                    if (!mergedNodesMap.has(node.id)) {
                        mergedNodesMap.set(node.id, { ...node });
                    }
                }
            });
        });

        rawNodes = Array.from(mergedNodesMap.values());
        rawLinks = Array.from(mergedLinksMap.values());

    } else {
        // SINGLE AGENT MODE (Standard)
        const graphData = stepData.graphs[currentAgent];
        if (graphData) {
            rawNodes = graphData.nodes.map(d => ({ ...d }));
            rawLinks = graphData.links.map(d => ({ ...d }));
        }
    }


    // --- POSITION PERSISTENCE ---
    const oldNodes = new Map(simulation.nodes().map(d => [d.id, d]));

    const nodes = rawNodes.map(d => {
        const existing = oldNodes.get(d.id);
        if (existing) {
            return { ...d, x: existing.x, y: existing.y, vx: existing.vx, vy: existing.vy };
        }
        return { ...d };
    });
    const links = rawLinks; // D3 will mutate these

    // --- NODES ---
    const node = nodeGroup.selectAll("circle")
        .data(nodes, d => d.id)
        .join(
            enter => enter.append("circle")
                .attr("r", 0)
                .attr("stroke", "#fff").attr("stroke-width", 1.5)
                .call(drag(simulation))
                .call(enter => enter.transition().duration(400).attr("r", d => d.radius)),
            update => update.transition().duration(400)
                .attr("r", d => d.radius)
                .attr("fill", d => d.id === "I" ? "#2196F3" : memoryScale(d.retrievability)),
            exit => exit.transition().duration(400).attr("r", 0).remove()
        );

    node.on("mouseover", (event, d) => {
        d3.select("#tooltip").style("opacity", 1)
            .html(`<strong>${d.id}</strong><br/>Stability: ${d.stability}<br/>Retrievability: ${d.retrievability}`)
            .style("left", (event.pageX + 10) + "px").style("top", (event.pageY - 20) + "px");
    }).on("mouseout", () => d3.select("#tooltip").style("opacity", 0));

    node.on("dblclick", (e, d) => { d.fx = null; d.fy = null; simulation.alpha(0.3).restart(); });

    // --- LINKS ---
    const link = linkGroup.selectAll("line")
        .data(links, d => `${d.source}-${d.target}-${d.label}`)
        .join("line")
        .attr("stroke", "#555").attr("stroke-width", 2).attr("marker-end", "url(#arrow)").attr("stroke-opacity", 0.6);

    // --- LABELS ---
    edgeLabelGroup.selectAll("g")
        .data(links, d => `${d.source}-${d.target}-${d.label}`)
        .join(
            enter => {
                const g = enter.append("g");
                g.append("rect").attr("rx", 3).attr("ry", 3).attr("fill", "#1a1a1a").attr("opacity", 0.8);
                g.append("text").text(d => d.label).attr("fill", "#ccc").attr("font-size", 9).attr("text-anchor", "middle").attr("dy", 3);
                return g;
            }, update => update, exit => exit.remove()
        );

    labelGroup.selectAll("text").data(nodes, d => d.id).join("text")
        .text(d => d.id).attr("font-size", 11).attr("fill", "#eee").attr("dx", 15).attr("dy", 4).style("text-shadow", "0 1px 2px black");

    simulation.nodes(nodes).on("tick", () => {
        link.attr("x1", d => d.source.x).attr("y1", d => d.source.y).attr("x2", d => d.target.x).attr("y2", d => d.target.y);
        node.attr("cx", d => d.x).attr("cy", d => d.y);
        labelGroup.selectAll("text").attr("x", d => d.x).attr("y", d => d.y);

        edgeLabelGroup.selectAll("g").attr("transform", d => {
            const sx = d.source.x, sy = d.source.y, tx = d.target.x, ty = d.target.y;
            if (sx === undefined || tx === undefined) return "";
            return `translate(${(sx + tx) / 2}, ${(sy + ty) / 2})`;
        });
        edgeLabelGroup.selectAll("rect").each(function() {
            const bbox = this.nextSibling.getBBox();
            d3.select(this).attr("x", bbox.x - 4).attr("y", bbox.y - 2).attr("width", bbox.width + 8).attr("height", bbox.height + 4);
        });
    });

    simulation.force("link").links(links);
    simulation.alpha(0.3).restart();
}

function drag(simulation) {
    function dragstarted(event) { if (!event.active) simulation.alphaTarget(0.3).restart(); event.subject.fx = event.subject.x; event.subject.fy = event.subject.y; }
    function dragged(event) { event.subject.fx = event.x; event.subject.fy = event.y; }
    function dragended(event) { if (!event.active) simulation.alphaTarget(0); event.subject.fx = null; event.subject.fy = null; }
    return d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended);
}
