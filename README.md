# Fantastic Physics

This is a weird simulation/math project that contains some made up physics laws. These laws can be found in the documentation folder. It is recommended to take a look at the introduction.txt file.

![Screenshot](/screenshots/screenshot-1.png)

---

# Contents:
- ./main.py will run a simulation that simulates *Fantastic Physics* laws.
- ./document_demo.py is just a demo that allows to read the documentation easier.
- ./libs/ contains some modules that the simulation uses.
  - ./libs/physics_lib.py contains the constants and the calculation methods.
  - ./libs/game_lib.py can be used to initiate the simulation.

- options.json contains some visual settings. Change them with caution.

---

# Simulation controls:

- **Left click** for moving the borders, particles *(bosons)* and the camera around.
- **Right click** for selecting particles and creating particles.
- **F** key will cause all the particles to stop.
- **T** key will show/hide the UI *(particle types, fps, energy meters)*.
- **a, b, c, x, y and z** keys will change the muons of the particle that will be created.
- **Space** key will make the simulation run/stop.
- **Mouse wheel** will make the camera zoom in/out.
- **+ and -** keys will increase/decrease the simulation time step.
- If a particle is selected, **D** key will only delete that particle.
- If no particles are selected, **D** key will delete all the particles.
