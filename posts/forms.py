from django import forms

from .models import Group, Post, Comment


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Поле не должно быть пустым.')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'cols': 3, 'rows': 2}),
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Комментарий не может быть пустым')
        return data
