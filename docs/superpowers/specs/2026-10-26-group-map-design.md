# Group map presentation

User-approved scope: colored circles at student locations, black pins at group
centroids, and a complete group member popup when a centroid pin is clicked.

Use existing Leaflet and backend centroids. Keep grouping, geocoding, state,
filters, exports, and exact student coordinates unchanged. Add an in-map color
legend and replace permanent group labels with hover/focus information.

Approaches: circles and legend alone was offered; the user chose circles plus
black centroid pins with complete member popups, matching their reference.

Presentation decisions: collocated students remain in a shared location popup;
concentric colored rings indicate their different groups (more than seven
groups use separate colored arcs to avoid hiding strokes or oversized rings). Exactly coincident
group centers share a pin whose popup contains each group's complete member
list, keeping every group accessible without inventing coordinates. Centroids
are labeled as group centers, never as meeting places or student addresses.
Popup lists scroll, use safe text, and support keyboard activation. Filtering
updates circles, center pins, and legend together; invalidation removes results.
