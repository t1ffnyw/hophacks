import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Executive Summary

    **Imagine it's 100 degrees outside. Is there shade on your block? A working air conditioner? Somewhere cooler to go?** In Baltimore, the answers depend on where you live. Across the city, the neighborhoods that heat up the most tend to be the ones with the fewest trees and the lowest household incomes, and they tend to rank higher for heat-related illness too. Same city, same afternoon, very different experiences.
    That divide isn't new. The 2019 investigation *Code Red: Baltimore's Climate Divide* documented how extreme heat compounds health challenges in communities with fewer resources and less protection. This notebook lets you see the pattern for yourself: pick a layer, or pair two, on the map, then use the what-if tool to add trees and watch what changes.
    By making these relationships visible, the project aims to support discussion about equitable heat protection and where further public-health investigation may be warranted.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Problem Statement

    **Who gets to stay cool?**

    When a heat wave hits, staying safe takes resources: shade, air conditioning, somewhere to go. *Code Red* showed that the places that heat up fastest are often the ones where those resources are scarcest.

    We ask that question of the data: **where in Baltimore do hotter conditions, limited tree canopy, lower household incomes, and higher heat-illness rankings overlap?**

    We build on earlier reporting in two ways. We put four measures side by side at the same neighborhood scale, and we add a what-if tool that asks what more trees could change. First, the ingredients.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Data Overview

    Our analysis brings together five datasets at a common geographic scale: Baltimore's 55 Community Statistical Areas (CSAs).

    | Dataset | What it measures | Source |
    |---|---|---|
    | CSA boundaries | Reference boundaries for Baltimore's Community Statistical Areas, used to join everything else | data.baltimorecity.gov |
    | Afternoon temperature | Modeled average afternoon temperature within each CSA | OSF |
    | Tree cover | Percent of each CSA covered by tree canopy | data.baltimorecity.gov |
    | Median household income | Median household income in each CSA | data.baltimorecity.gov |
    | Heat-Related Illness | A percentile rank for each ZIP code | ATSDR |
    |

    Now, let's look at the map.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Insight Synthesis

    1. **Lower-income neighborhoods tend to have fewer trees.**

    2. **Fewer trees tend to mean hotter afternoons.**

    3. **The hotter, less shaded places tend to rank higher for  heat-related illnesses.**

    **Putting it all together.** Some neighborhoods are hot, short on trees, low on income, and high on the illness ranking. If shade is added somewhere, these are natural places to look at first.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Discussion

    **What the what-if tool is.** It lets you add tree cover to one neighborhood and see how afternoon temperature might change. It borrows the pattern we found across Baltimore, where leafier neighborhoods tend to be cooler, and applies it to estimate the effect. Think of it as a way to feel the pattern, not a forecast for any particular block.


    **What we can and cannot conclude.**
    - **Correlation is not causation.** Neighborhoods with more trees may also differ in other ways that affect heat, such as housing age, the amount of pavement and buildings, industrial land, nearby highways, and access to air conditioning.
    - **The what-if estimate is simple.** It applies a single average relationship to every neighborhood. In practice, the cooling from new trees depends on where they are planted, how large they grow, and what surrounds them, and young trees take years to provide shade.
    - **Our illness measure is coarse.** It's a percentile rank by ZIP code, so it can't tell us how many people were affected, and matching ZIPs to CSAs is approximate.


    **Where we'd go next**

    1. **Get neighborhood-level illness counts,** ideally from the city or state health department, to test whether these patterns hold up in actual cases.
    2. **Account for other factors.** Replace our simple comparison with a model that includes income, pavement and building coverage, and housing age, to separate the effect of trees from everything that travels with them.
    3. **Make the what-if tool more realistic.** Add where trees can physically be planted, what it costs, and how long trees take to grow, and check the projections against neighborhoods that have actually gained trees.
    4. **Involve residents.** Communities know where people go to cool off and where shade is missing. Their input should shape where any planting happens.


    Trees are one tool among many, but they matter for health as well as comfort. Shade and cooler air can lower the heat people are exposed to, and heat is hardest on those with heart, kidney, and lung conditions. Cooling centers, help paying for air conditioning, and outreach to older and isolated neighbors matter too. But whether there's shade on your block shouldn't depend on where you live.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reflection

    ### Feedback on marimo

    **What worked well.** Reactivity was the best part. When a dropdown or slider changes, the map updates with no callback code, which made the what-if tool much easier to build than it would have been in a traditional notebook. Notebooks being plain `.py` files also let us collaborate with git as a team and mirror our GitHub repo in molab for sharing.

    **What was hard.** Setting up the environment in VS Code took us a while, and errors in VS Code's notebook view were also confusing, since it wasn't always clear that the problem wasn't our code.

    ### Working with AI tools

    We used Claude to plan the notebook and divide the work, and Grok through Cursor to build many of the visuals, including the map and slider code.

    **What it sped up.** It turned our idea of a single map where you pick up to two variables into working code much faster than we could have alone.

    **What it got wrong.** Sometimes it didn't execute our vision properly, and the interface it produced could be difficult to follow. We decided to redesign the map legends so the data was easier to read at a glance. We had to read the errors, fix the code, or go back and re-prompt.

    **What we learned about prompting.** Specific prompts worked much better than vague ones. Our habits were to ask for one change at a time, state marimo's rules up front, check every result against our real data, and paste the exact error message when something broke. The tools were fast at drafts, but knowing our data and catching mistakes stayed our job.
    """)
    return


if __name__ == "__main__":
    app.run()
