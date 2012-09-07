from math import ceil

from datetime import tzinfo, timedelta, datetime
class FixedTimezone(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset):
        self.__offset = timedelta(minutes = offset)
        self.__name = str(offset)

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return timedelta(0)



from furl import furl

class GithubLinker():
    def __init__(self, project_path, default_branch=None):
        if not default_branch:
            default_branch = 'production'
        self.default_branch = default_branch
        self.project_path = project_path

    def furl(self):
        return furl(self.project_path)

    def to_project(self):
        return self.furl().url

    def to_commit(self, ref):
        if not ref:
            return ''
        return self.furl().add(path='commit/' + str(ref)).url

    def to_file(self, path, ref=None, line=None):
        fragment = ''
        if not ref:
            ref = self.default_branch
        if line:
            fragment = 'L' + str(line)

        return self.furl().add(path='tree/'+str(ref)+'/'+path).set(fragment=fragment).url

    def to_diff(self, from_ref, to_ref):
        return self.furl().add(path='compare/'+ str(from_ref) + '...' + str(to_ref)).url



class Paginator:

    def __init__(self, queryset, size_per_page, current_page):
        self.count = queryset.count()
        self.queryset = queryset
        self.size_per_page = size_per_page

        current_page = int(current_page)

        if current_page < 1:
            current_page = 1

        self.current_page = current_page

    def get_current_page(self):
        offsetX = (self.current_page - 1) * self.size_per_page
        offsetY = offsetX + self.size_per_page
        return self.queryset[offsetX:offsetY]

    def get_num_pages(self):
        return int(ceil(self.count / float(self.size_per_page)))

    def get_first(self):
        return 1

    def get_last(self):
        return self.get_num_pages()

    def has_prev(self):
        return self.current_page > 1

    def has_next(self):
        return self.current_page < self.get_num_pages()

    def get_current_page_number(self):
        return self.current_page
