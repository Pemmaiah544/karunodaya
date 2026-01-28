from django import forms
from django.utils.safestring import mark_safe
from .models import Book


class CoverImageWidget(forms.widgets.FileInput):
    """Custom widget that shows file input and small preview area"""
    
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        
        # Add CSS class and ID
        attrs['class'] = attrs.get('class', '') + ' cover-image-input'
        attrs['accept'] = 'image/*'
        input_id = f'id_{name}'
        attrs['id'] = input_id
        
        # Render the file input
        file_input = super().render(name, value, attrs, renderer)
        
        # Preview area - small and compact
        if hasattr(self, 'current_image_html'):
            preview_html = self.current_image_html
        else:
            preview_html = f'''
            <div class="cover-preview" style="
                margin-top: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 80px;
                height: 100px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f5f5f5;
                color: #999;
                font-size: 10px;
                text-align: center;
                overflow: hidden;
                position: relative;
            ">
                <img id="{input_id}_preview" src="" alt="" style="
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: none;
                ">
                <button id="{input_id}_clear" type="button" style="
                    position: absolute;
                    top: 2px;
                    right: 2px;
                    width: 16px;
                    height: 16px;
                    border: none;
                    background: rgba(255, 255, 255, 0.9);
                    color: #666;
                    border-radius: 50%;
                    cursor: pointer;
                    font-size: 10px;
                    display: none;
                    align-items: center;
                    justify-content: center;
                    line-height: 1;
                ">&times;</button>
                <span id="{input_id}_placeholder">No image</span>
            </div>
            <script>
            document.getElementById('{input_id}').addEventListener('change', function(e) {{
                const file = e.target.files[0];
                const preview = document.getElementById('{input_id}_preview');
                const placeholder = document.getElementById('{input_id}_placeholder');
                const clearBtn = document.getElementById('{input_id}_clear');
                
                if (file) {{
                    const reader = new FileReader();
                    reader.onload = function(e) {{
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                        placeholder.style.display = 'none';
                        clearBtn.style.display = 'flex';
                    }};
                    reader.readAsDataURL(file);
                }} else {{
                    preview.style.display = 'none';
                    placeholder.style.display = 'block';
                    clearBtn.style.display = 'none';
                }}
            }});
            
            document.getElementById('{input_id}_clear').addEventListener('click', function() {{
                document.getElementById('{input_id}').value = '';
                document.getElementById('{input_id}_preview').style.display = 'none';
                document.getElementById('{input_id}_placeholder').style.display = 'block';
                this.style.display = 'none';
            }});
            </script>
            '''
        
        return mark_safe(file_input + preview_html)


class BookAdminForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'cover_image': CoverImageWidget()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # For existing books with cover images
        if self.instance and self.instance.pk and self.instance.cover_image:
            current_image_html = f'''
            <div class="cover-preview" style="
                margin-top: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 80px;
                height: 100px;
                overflow: hidden;
            ">
                <img src="{self.instance.cover_image.url}" 
                     width="80" 
                     height="100" 
                     style="object-fit: cover;" 
                     alt="Current cover">
            </div>
            '''
            
            self.fields['cover_image'].widget.current_image_html = current_image_html
