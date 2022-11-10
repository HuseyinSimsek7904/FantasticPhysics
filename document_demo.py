from libs import document_lib, vector_lib
import pygame

pygame.init()


def update_page():
    global main_surface, surface

    try:
        document_viewer.load_escapes()
        main_surface = document_viewer.convert_file_to_mathematical(file_name, 1)
        surface = pygame.transform.rotozoom(main_surface, 0, size)

    except Exception as e:
        print(e)


document_viewer = document_lib.DocumentViewer((0, 0, 0), (255, 255, 255))

file_name = "json_documentation/" + input("Section: ") + ".json"

camera_pos = vector_lib.Vector(0, 0)
size = 1

main_surface = pygame.Surface((500, 500))
surface = pygame.Surface((500, 500))
window = pygame.display.set_mode((500, 500))
update_page()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                update_page()

        elif event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0]:
                camera_pos.add_(*event.rel, -1)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_WHEELUP:
                size *= 5 / 4
                surface = pygame.transform.rotozoom(main_surface, 0, size)

            elif event.button == pygame.BUTTON_WHEELDOWN:
                size *= 4 / 5
                surface = pygame.transform.rotozoom(main_surface, 0, size)

    window.fill((0, 0, 0))
    window.blit(surface, (-camera_pos).int_tuple)
    pygame.display.update()
