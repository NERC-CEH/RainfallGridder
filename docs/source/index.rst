.. _index:

:layout: landing


.. container::
    :name: home-head

    .. image:: /_static/rainfall_gridder_logo_circle.png
        :alt: RainfallGridder
        :width: 350
    

    .. container::

        .. raw:: html

            <h1>RainfallGridder</h1>
            <h2>Interpolate rain gauge data onto regular grids</h2>

        .. container:: badges
           :name: badges

           .. image:: https://img.shields.io/badge/Humans-999999?style=flat&logo=Made by&label=Made By&labelColor=2BD962
              :alt: Made by humans

           .. image:: https://badges.frapsoft.com/os/v1/open-source.svg?v=103
              :alt: Open Source
              
           .. image:: https://img.shields.io/badge/License-GPLv3-blue.svg
              :alt: GPL v3 License

           .. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
              :alt: UV

           .. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
              :alt: Ruff Version



.. rst-class:: lead




.. container:: buttons

    `Docs <installation.html>`_
    `Usage <usage.html>`_
    `GitHub <https://github.com/NERC-CEH/RainfallGridder/>`_

.. grid:: 1 1 2 3
    :class-row: surface
    :padding: 0
    :gutter: 2

    .. grid-item-card:: :octicon:`repo-template` Getting Started
      :link: usage.html

      A collection of tutorials for setting up and using RainfallGridder. 

    .. grid-item-card:: :octicon:`alert` Issues
      :link: https://github.com/NERC-CEH/RainfallGridder/issues

      Use this link you need to report any bugs or request new features.

    .. grid-item-card:: :octicon:`people` More FDRI projects
      :link: https://github.com/NERC-CEH/

      Learn more about the UK's Floods & Droughts Research Infrastructure Project.


What is RainfallGridder?
========================

RainfallGridder provides a user-friendly processing pipeline for generating gridded rainfall data.
It is motivated by the need to make workflows for generating high-resolution gridded rainfall data products more *open* and *extendable*.
It will be deployed to generate CEH-GEAR 15 min (an extension of the `CEH-GEAR 1h product <https://catalogue.ceh.ac.uk/documents/fc9423d6-3d54-467f-bb2b-fc7357a3941f>`_ developed out of UKCEH).
RainfallGridder is built on top of `Polars <https://docs.pola.rs/>`_, which handles efficient DataFrame processes (like Pandas, but quicker).

The original methodology for CEH-GEAR 1h forms the outline of the pipeline this package provides. That is a 4-step procedure for:
        1. Preparing your rain gauge data for gridding (combining duplicates by location).
        2. Quality controlling rain gauge data with `RainfallQC <https://github.com/NERC-CEH/RainfallQC>`_ and the `IntenseQC rulebase <https://www.sciencedirect.com/science/article/pii/S1364815221002127#tbl2>`_.
        3. Correlating values daily sums of rain gauges to nearest daily gridded rainfall.
        4. Generating grids using nearest-neighbour interpolation.


.. container:: image-row

   .. container:: image-item

      .. figure:: _static/ukceh_logo_light.png
         :alt: UKCEH
         :height: 100px
         :target: https://www.ceh.ac.uk

   .. container:: image-item

      .. figure:: _static/fdri_logo.png
         :alt: FDRI
         :height: 100px
         :target: https://fdri.org.uk


Community
=========

Developed at `UKCEH <https://www.ceh.ac.uk/>`_, welcoming community engagement and contributions.

License
=======

This project is licensed under the `GNU GPL v3.0 <https://github.com/NERC-CEH/RainfallGridder/raw/branch/main/LICENSE>`_.


.. toctree::
    :hidden:
    :maxdepth: 2
    :caption: Getting started

    installation
    usage

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: API reference

    api

.. toctree::
    :hidden:
    :maxdepth: 1
    :caption: Community

    contributing
    codeofconduct


.. Current version: |release|

