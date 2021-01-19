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


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'cols': 3, 'rows': 2}),
        }
