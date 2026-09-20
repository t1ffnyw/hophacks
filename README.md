# The Cost of No Shade 🌳 🌳 🌳

**Executive Summary**

Imagine it's 100 degrees outside. Is there shade on your block? A working air conditioner? Somewhere cooler to go? In Baltimore, the answers depend on where you live. Across the city, the neighborhoods that heat up the most tend to be the ones with the fewest trees and the lowest household incomes, and they tend to rank higher for heat-related illness too. Same city, same afternoon, very different experiences.

That divide isn't new. The 2019 investigation Code Red: Baltimore's Climate Divide documented how extreme heat compounds health challenges in communities with fewer resources and less protection. This notebook lets you see the pattern for yourself: pick a layer, or pair two, on the map, then use the what-if tool to add trees and watch what changes.

By making these relationships visible, the project aims to support discussion about equitable heat protection and where further public-health investigation may be warranted.

**Problem Statement**

Who gets to stay cool?

When a heat wave hits, staying safe takes resources: shade, air conditioning, somewhere to go. Code Red showed that the places that heat up fastest are often the ones where those resources are scarcest.

We ask that question of the data: where in Baltimore do hotter conditions, limited tree canopy, lower household incomes, and higher heat-illness rankings overlap?

We build on earlier reporting in two ways. We put four measures side by side at the same neighborhood scale, and we add a what-if tool that asks what more trees could change. 

**Tools and Libraries**

Data Preparation & Analysis: We relied on pandas to load, clean, filter, and merge all 4 source datasets into one unified Community Statistical Area (CSA)-level table. Once the data was combined, we used statsmodels to fit the OLS linear regression linking tree canopy to heat-illness percentile, which powers the what-if tool's live predictions, and geopandas to join CSA boundary geometry onto our combined table so it could actually be rendered as a map.

On the visualization side, the entire interactive experience runs inside marimo, a reactive Python notebook framework, with folium handling the interactive choropleth map itself and its neighborhood-level popups.

Our underlying data was pulled from several sources: CSA boundaries, tree cover, and median household income all come from Baltimore's Open Data Portal (data.baltimorecity.gov); modeled afternoon temperature by CSA comes from OSF; and heat-related illness percentiles by ZIP code come from ATSDR's Heat & Health Index. Since that last dataset is reported by ZIP code rather than CSA, we used a ZIP-to-CSA crosswalk table from the mapbaltimore R package to reconcile its geography with the rest of our data before merging everything together.

⭐ **Goal** ⭐

Tree cover is often talked about as an environmental amenity — but our data shows it's a public health variable with real, measurable stakes. Our aim is to bring attention to this often unthought-of consequence of a lack of tree cover, and to advocate for more tree planting in low-income, heat-stressed neighborhoods across Baltimore. 

