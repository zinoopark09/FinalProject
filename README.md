# RQLIB
## Requirements and Libraries Finder
## Overview
### Final Project, 2019 FALL, CSCI E-29
#### Gabriel Guillen, Zinoo Park

Wouldn't it be nice if we had a way of knowing which requirements and libraries were installed or not installed where ?
It is every so annoying to find your app working at home only to find that it breaks down on Travis just because
a library or a module was not included in the Pipfile.

The features designed are as below:

1. Find libraries installed in MAIN & libraries installed via PIPENV

2. Find where the dependencies are installed. Pathwise.

3. Show Dependency Tree

4. Convert Pipfiles to Travis versions

### Final Deliverable

The end product is an app that can be executed from the command line, in which you can select a folder or environment
to analyze.

### To Run
In terminal (not pipenv shell),
'python -m rqlib'


### Limitations and Challenges

Due to time constraint, it was only possible to develop for only one specific virtual environment or OS. In this case,
in Anaconda on Windows. However, given enough resources, it may be easy to scale.



