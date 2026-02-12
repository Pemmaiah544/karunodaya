from django.contrib import admin

class AdminPaginationMixin:
    """
    Mixin to provide enhanced pagination with per-page selection.
    Must be used with 'admin/catalog/enhanced_book_clean.html' template.
    """
    change_list_template = 'admin/catalog/enhanced_book_clean.html'
    change_form_template = 'admin/base_change_form.html'

    def changelist_view(self, request, extra_context=None):
        # Store per_page parameter before modifying GET
        original_get = request.GET
        per_page_value = original_get.get('per_page')
        
        # Remove per_page from GET to avoid Django treating it as filter
        cleaned = original_get.copy()
        if 'per_page' in cleaned:
            del cleaned['per_page']
        
        request.GET = cleaned
        
        try:
            response = super().changelist_view(request, extra_context=extra_context)
            # Apply per_page to the ChangeList and re-fetch results
            if hasattr(response, 'context_data') and 'cl' in response.context_data:
                cl = response.context_data['cl']
                allowed = {"5": 5, "10": 10, "25": 25, "50": 50}
                if per_page_value in allowed:
                    cl.list_per_page = allowed[per_page_value]
                    cl.get_results(request)
                    response.context_data['per_page'] = str(cl.list_per_page)
                else:
                    response.context_data['per_page'] = str(self.list_per_page)
                
                # Calculate result start and end for "Showing X to Y of Z"
                # In Django 5.1+ and Unfold, ChangeList.page_num is 1-indexed.
                page_num = cl.page_num
                start = ((page_num - 1) * cl.list_per_page) + 1
                end = min(page_num * cl.list_per_page, cl.result_count)
                
                # Ensure start is not greater than result_count for empty results
                if cl.result_count == 0:
                    start = 0
                    end = 0
                
                response.context_data['cl'].result_start = start
                response.context_data['cl'].result_end = end
                
            return response
        finally:
            request.GET = original_get
