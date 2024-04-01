# DSM_PV_EV_Integration
Simulation toolkit for comprehensive study on the integration of demand side management (DSM) strategies, renewable systems, and smart charging infrastructure for electric vehicles.

**Main Execution File**: The core of this simulation framework to be executed is **Main.py**. This script is configured with default parameters that can be modified as per user requirements. Parameters within Main.py allow for customization and experimentation with different DSM strategies, PV generation profiles, and EV charging schemes.

**Dependencies**
On top of widely used Python libraries (as in numpy and pandas), the following specific packages are also required to use all the functionalities:
- **pyxlsb**: For reading Excel binary files.
- **pyomo**: A library for optimization modeling.
- **IPOPT, BONMIN**: Solvers for optimization, necessary for some simulation scenarios.
