

def allocate_values_to_nested_list(values: list, length_of_nested_list: int):
    new_list = []
    for i, value in enumerate(values):
        if i % length_of_nested_list == 0:
            new_list.append([])
        new_list[-1].append(value)
    return new_list

class PagedList():
    def __init__(self, objects: list, page_size: int):
        self.objects = objects
        self.page_size = page_size
        self._page = 0
        self.pages = allocate_values_to_nested_list(self.objects, self.page_size)
        self.pages_amount = len(self.pages)

    def current_page(self):
        return self.pages[self._page]
    def _change_page(self, pages: int):
        self._page += pages
        if self._page not in range(self.pages_amount):
            raise ValueError('Pages out of range')
    def page_up(self):
        self._change_page(1)
    def page_down(self):
        self._change_page(-1)
    def is_page_last(self):
        return self._page == self.pages_amount - 1
    def is_page_first(self):
        return self._page == 0
