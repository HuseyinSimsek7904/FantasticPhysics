# Fantastic Physics

This is a weird simulation/math project that contains some made up physics laws. These laws can be found in the documentation folder. It is recommended to take a look at the introduction.txt file.

---

# Contents:
- ./main.py will run a simulation that simulates *Fantastic Physics* laws.
- ./document_demo.py is a demo program that allows to read the documentation easier.
- ./tiller_series_renderer_demo.py is a demo program that calculates tiller series to a certain depth.
- ./options.json contains some visual settings. Change them with caution.
- ./libs/ contains some modules that the simulation uses.
  - ./libs/physics_lib.py contains the constants and the calculation methods.
  - ./libs/complex_physics_lib.py contains more advanced tools for calculation.
  - ./libs/game_lib.py can be used to initiate the simulation.
  - ./libs/widgets_lib.py contains some custom widgets.

---

# Simulation controls:

- **Left click** for moving the borders, particles *(bosons)* and the camera around.
- **Right click** for selecting particles and creating particles.
- **CTRL + Right click** for selecting multiple particles.
- **CTRL + Left Click** for selecting using a selection box.
- **F** key will cause all the particles to stop.
- **T** key will show/hide the UI *(particle types, fps, energy meters)*.
- **a, b, c, x, y and z** keys will change the muons of the particle that will be created.
- **Space** key will make the simulation run/stop.
- **Mouse wheel** will make the camera zoom in/out.
- **+ and -** keys will increase/decrease the simulation time step.
- **R** key will delete all particles and create random particles. Number of particles is equal to the area.
