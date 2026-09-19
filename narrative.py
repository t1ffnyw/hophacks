import marimo

__generated_with = "0.24.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##Executive Summary

    Imagine it's 100 degrees outside. Is there shade on your block? A working air conditioner? Somewhere cooler to go? In Baltimore, the answers depend on where you live. Baltimore faces a heat divide, a phenomenon where historically low-income neighborhoods experience higher summer temperatures. The 2019 investigation Code Red: Baltimore’s Climate Divide documented how extreme heat compounds health challenges in communities with fewer resources and less protection from the heat.
    Inspired by that reporting, our interactive marimo notebook explores how tree coverage, temperature, household income, and heat-related illnesses overlap across Baltimore. You can investigate where limited shade and economic disadvantage coincide with hotter conditions—patterns that matter for understanding vulnerability to heat-related illness.
    By making these relationships visible, the project aims to support discussion about equitable heat protection and where further public-health investigation may be warranted.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##Problem Statement

    Who has the resources and surroundings to stay safe during extreme heat? Baltimore’s Code Red investigation showed how heat can threaten health while placing an unequal burden on communities already facing economic and health challenges.
    Understanding vulnerability to heat-related illness requires examining both the conditions people face and the resources available to protect them. Our central question is: Where in Baltimore do hotter conditions, limited tree canopy, lower household incomes, and heat-related illnesses overlap?
    We bring these datasets together at a common geographic scale and use interactive visualizations to make community comparisons accessible. The analysis identifies overlapping environmental and economic conditions that warrant attention, while distinguishing measured temperatures and canopy coverage from health-risk indicators and recorded illness outcomes.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Data Overview

    Our analysis brings together four datasets at a common geographic scale: Baltimore's 55 Community Statistical Areas (CSAs).

    | Dataset | What it measures |
    |---|---|
    | CSA boundaries | Reference boundaries for Baltimore's Community Statistical Areas, used to join everything else |
    | Afternoon temperature | Modeled average afternoon temperature within each CSA |
    | Tree cover | Percent of each CSA covered by tree canopy |
    | Median household income | Median household income in each CSA |
    | Heat-Related Illness | Number of reported heat-related illnesses|
    |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Insight Synthesis

    1. **Neighborhoods with less tree cover have higher temperatures.**

    2. **Neighborhoods with less tree cover tend to have more heat-related illnesses.**

    3. **Lower-income neighborhoods tend to have fewer trees and more heat.**
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Discussion

    **What the "what if" map shows.** Our what-if tool lets you add tree cover to one neighborhood and see how afternoon temperature might change. It uses the relationship we found across Baltimore's neighborhoods, where areas with more trees tend to be cooler, to estimate the effect. It is meant to make the pattern tangible and to show where added shade could matter most.


    **What we can and cannot conclude.**
    - **Correlation is not causation.** Neighborhoods with more trees may also differ in other ways that affect heat, such as housing age, the amount of pavement and buildings, industrial land, nearby highways, and access to air conditioning.
    - **The what-if estimate is simple.** It applies a single average relationship to every neighborhood. In practice, the cooling from new trees depends on where they are planted, how large they grow, and what surrounds them, and young trees take years to provide shade.


    **Next steps**
    1. **Account for other factors.** Replace our simple comparison with a model that includes income, building and pavement coverage, and housing age, to separate the effect of trees from everything else that travels with them.
    2. **Make the what-if tool more realistic.** Add where trees can physically be planted, what it costs, and how long it takes them to grow, and check the projections against neighborhoods that have actually gained trees over time.
    3. **Involve residents.** Communities know where people go to cool off and where shade is missing. Their input should shape where any planting happens.


    Heat is a health and equity issue, and trees are only one part of the response. Cooling centers, help paying for air conditioning, and outreach to older and isolated residents matter too.
    """)
    return


if __name__ == "__main__":
    app.run()
