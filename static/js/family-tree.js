// D3.js Hierarchical Family Tree Visualization

// Initialize the visualization when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the family tree page
    const treeContainer = document.getElementById('family-tree-visualization');
    if (!treeContainer) return;
    
    // Fetch family tree data from the API
    fetch('/api/family-tree-data')
        .then(response => response.json())
        .then(data => createHierarchicalFamilyTree(data, treeContainer))
        .catch(error => console.error('Error fetching family tree data:', error));
});

function createHierarchicalFamilyTree(data, container) {
    // Clear any existing content
    container.innerHTML = '';
    
    // Set dimensions and margins
    const margin = {top: 80, right: 90, bottom: 50, left: 90};
    const width = container.offsetWidth - margin.left - margin.right;
    const height = 600 - margin.top - margin.bottom;
    
    // Create SVG container
    const svg = d3.select(container)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);
    
    // Convert the flat data structure to a hierarchical structure
    // First, find the root node (we'll assume it's the one with no parents)
    let rootNode = findRootNode(data);
    
    // If we couldn't find a clear root, just use the first node
    if (!rootNode && data.nodes.length > 0) {
        rootNode = data.nodes[0];
    }
    
    // Create the hierarchy
    const hierarchyData = createHierarchy(rootNode, data);
    
    // Create a tree layout
    const treeLayout = d3.tree()
        .separation((a, b) => {
            const distance = a.depth - b.depth;
            return distance > 0 ? 50 : 20;
        })
        .size([width, height - 100]);
        
    
    // Apply the layout to our hierarchy data
    const treeData = treeLayout(d3.hierarchy(hierarchyData));
    
    const existingNodeIds = new Set(treeData.descendants().map(n => n.data.id));

    const missingSpouses = data.links
        .filter(link => link.type === 'Spouse')
        .flatMap(link => {
            const nodesToAdd = [];
            if (!existingNodeIds.has(link.source)) {
                const person = data.nodes.find(n => n.id === link.source);
                if (person) nodesToAdd.push({ ...person });
            }
            if (!existingNodeIds.has(link.target)) {
                const person = data.nodes.find(n => n.id === link.target);
                if (person) nodesToAdd.push({ ...person });
            }
            return nodesToAdd;
        });

    // Give fake x/y to start with (you can position relative to their partner later)
    const allNodes = [
        ...treeData.descendants(),
        ...missingSpouses.map(spouse => {
            const partnerLink = data.links.find(link =>
                link.type === 'Spouse' &&
                (link.source === spouse.id || link.target === spouse.id)
            );
            const partnerId = partnerLink?.source === spouse.id ? partnerLink?.target : partnerLink?.source;
            const partnerNode = treeData.descendants().find(n => n.data.id === partnerId);
    
            return {
                x: partnerNode ? partnerNode.x - 100 : 0,
                y: partnerNode ? partnerNode.y : 0,
                data: spouse
            };
        })
    ];
    

    // missingSpouses.forEach(spouse => {
    //     const partnerLink = data.links.find(link =>
    //         link.type === 'Spouse' &&
    //         (link.source === spouse.id || link.target === spouse.id)
    //     );
    //     if (partnerLink) {
    //         const partnerId = partnerLink.source === spouse.id ? partnerLink.target : partnerLink.source;
    //         const partnerNode = treeData.descendants().find(n => n.data.id === partnerId);
    //         if (partnerNode) {
    //             spouse.x = partnerNode.x + 80; // offset to the right
    //             spouse.y = partnerNode.y;
    //         }
    //     }
    // });
    

    // Define relationship colors
    const relationshipColors = {
        'Spouse': '#FFC107',
        'Parent': '#009688',
    };
    
    // Default color for unknown relationship types
    const defaultColor = '#999999';
    
    // Create links between nodes
    const link = svg.selectAll(".link")
        .data(treeData.links())
        .enter()
        .append("path")
        .attr("class", "link")
        .attr("d", d3.linkVertical()
            .x(d => d.x)
            .y(d => d.y))
        .attr("fill", "none")
        .attr("stroke", d => {
            // Find the original link to get its type
            const originalLink = data.links.find(link => 
                (link.source === d.source.data.id && link.target === d.target.data.id) ||
                (link.source === d.target.data.id && link.target === d.source.data.id)
            );
            return originalLink ? (relationshipColors[originalLink.type] || defaultColor) : defaultColor;
        })
        .attr("stroke-width", 2);

    // Draw spouse links (horizontal, same level)
    const spouseLinks = data.links.filter(link => link.type === 'Spouse');

    svg.selectAll(".spouse-link")
    .data(spouseLinks)
    .enter()
    .append("line")
    .attr("class", "spouse-link")
    .attr("x1", d => {
        const sourceNode = allNodes.find(n => n.data.id === d.source);
        return sourceNode ? sourceNode.x : 0;
    })
    .attr("y1", d => {
        const sourceNode = allNodes.find(n => n.data.id === d.source);
        return sourceNode ? sourceNode.y : 0;
    })
    .attr("x2", d => {
        const targetNode = allNodes.find(n => n.data.id === d.target);
        return targetNode ? targetNode.x : 0;
    })
    .attr("y2", d => {
        const targetNode = allNodes.find(n => n.data.id === d.target);
        return targetNode ? targetNode.y : 0;
    })
    .attr("stroke", "#FF4081") // nice pinkish color for spouse links
    .attr("stroke-width", 2)
    .attr("stroke-dasharray", "4,2"); // dashed line for visibility

    svg.selectAll(".debug-spouse")
    .data(allNodes.filter(n => n.data.gender === "female")) // or filter by those manually added
    .enter()
    .append("circle")
    .attr("class", "debug-spouse")
    .attr("cx", d => d.x)
    .attr("cy", d => d.y)
    .attr("r", 4)
    .attr("fill", "red");



    // Optional: tweak node x-positions to bring spouses closer (for aesthetics)
    // spouseLinks.forEach(link => {
    //     const sourceNode = treeData.descendants().find(n => n.data.id === link.source);
    //     const targetNode = treeData.descendants().find(n => n.data.id === link.target);
    //     if (sourceNode && targetNode && sourceNode.y === targetNode.y) {
    //         const avgX = (sourceNode.x + targetNode.x) / 2;
    //         sourceNode.x = avgX - 40;
    //         targetNode.x = avgX + 40;
    //     }
    // });

    missingSpouses.forEach(spouse => {
        const partnerLink = data.links.find(link =>
            link.type === 'Spouse' &&
            (link.source === spouse.id || link.target === spouse.id)
        );
        const partnerId = partnerLink.source === spouse.id ? partnerLink.target : partnerLink.source;
        const partnerNode = treeData.descendants().find(n => n.data.id === partnerId);
    
        if (partnerNode) {
            spouse.x = partnerNode.x + 300; // offset right
            spouse.y = partnerNode.y;
        }
    });
    

    const nodeGroup = svg.selectAll(".node")
    .data(allNodes)
    .enter()
    .append("g")
    .attr("class", "node")
    .attr("transform", d => `translate(${d.x},${d.y})`);
    
    // Add circles for each node
    nodeGroup.append("circle")
        .attr("r", 25)
        .attr("fill", d => d.data.gender === 'Male' ? '#7EB6FF' : 
                           (d.data.gender === 'Female' ? '#FFAFD7' : '#B5B5B5'));
    
    // Add text labels (names)
    nodeGroup.append("text")
        .text(d => d.data.name)
        .attr("text-anchor", "middle")
        .attr("dy", 40)
        .attr("font-size", "12px");
    
    // Add tooltips
    nodeGroup.append("title")
        .text(d => {
            let tooltip = `${d.data.name}\n`;
            if (d.data.birthDate) tooltip += `Born: ${d.data.birthDate}\n`;
            if (d.data.deathDate) tooltip += `Died: ${d.data.deathDate}\n`;
            if (d.data.occupation) tooltip += `Occupation: ${d.data.occupation}`;
            return tooltip;
        });
    
    // Add zoom capability
    const zoom = d3.zoom()
        .scaleExtent([0.5, 3])
        .on("zoom", (event) => {
            svg.attr("transform", event.transform);
        });
    
    d3.select(container).select("svg")
        .call(zoom);
}

// Function to find the root node (node with no parents)
function findRootNode(data) {
    const childrenIds = new Set(data.links.map(link => link.target));
    
    // Find nodes that are not children of any other node
    const potentialRoots = data.nodes.filter(node => !childrenIds.has(node.id));
    
    // Return the first potential root (or null if none found)
    return potentialRoots.length > 0 ? potentialRoots[0] : null;
}

// Function to create a hierarchical structure from flat data
function createHierarchy(rootNode, data, visited = new Set()) {
    if (!rootNode || visited.has(rootNode.id)) return null;
    visited.add(rootNode.id);

    const hierarchyNode = {
        id: rootNode.id,
        name: rootNode.name,
        gender: rootNode.gender,
        birthDate: rootNode.birthDate,
        deathDate: rootNode.deathDate,
        occupation: rootNode.occupation,
        children: []
    };

    const parentLinks = data.links.filter(link => link.source === rootNode.id && link.type === 'Parent');

    parentLinks.forEach(link => {
        const childNode = data.nodes.find(node => node.id === link.target);
        if (childNode) {
            const childHierarchy = createHierarchy(childNode, data, visited);
            if (childHierarchy) {
                hierarchyNode.children.push(childHierarchy);
            }
        }
    });

    return hierarchyNode;
}


function createLegend(svg, colors, width) {
    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${width - 180}, -40)`);
    
    let yOffset = 0;
    Object.entries(colors).forEach(([type, color], i) => {
        const legendRow = legend.append("g")
            .attr("transform", `translate(0, ${yOffset})`);
        
        legendRow.append("rect")
            .attr("width", 14)
            .attr("height", 14)
            .attr("fill", color);
        
        legendRow.append("text")
            .attr("x", 20)
            .attr("y", 12)
            .text(type)
            .style("font-size", "12px");
        
        yOffset += 20;
    });
}