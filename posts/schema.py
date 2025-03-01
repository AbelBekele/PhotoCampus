import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.contrib.auth.models import User
from .models import Post, Comment, Like, Share

# Define Types
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'posts', 'comments', 'likes', 'shares')

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = '__all__'
        filter_fields = {
            'title': ['exact', 'icontains', 'istartswith'],
            'content': ['icontains'],
            'author__username': ['exact'],
            'created_at': ['exact', 'gt', 'lt'],
        }
        interfaces = (graphene.relay.Node,)

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = '__all__'
        filter_fields = {
            'content': ['icontains'],
            'author__username': ['exact'],
            'post__id': ['exact'],
            'created_at': ['exact', 'gt', 'lt'],
        }
        interfaces = (graphene.relay.Node,)

class LikeType(DjangoObjectType):
    class Meta:
        model = Like
        fields = '__all__'
        filter_fields = {
            'user__username': ['exact'],
            'post__id': ['exact'],
        }
        interfaces = (graphene.relay.Node,)

class ShareType(DjangoObjectType):
    class Meta:
        model = Share
        fields = '__all__'
        filter_fields = {
            'user__username': ['exact'],
            'post__id': ['exact'],
            'shared_with': ['exact', 'icontains'],
            'created_at': ['exact', 'gt', 'lt'],
        }
        interfaces = (graphene.relay.Node,)

# Query
class Query(graphene.ObjectType):
    # Single item queries
    post = graphene.relay.Node.Field(PostType)
    comment = graphene.relay.Node.Field(CommentType)
    like = graphene.relay.Node.Field(LikeType)
    share = graphene.relay.Node.Field(ShareType)
    
    # List queries
    all_posts = DjangoFilterConnectionField(PostType)
    all_comments = DjangoFilterConnectionField(CommentType)
    all_likes = DjangoFilterConnectionField(LikeType)
    all_shares = DjangoFilterConnectionField(ShareType)
    
    def resolve_all_posts(self, info, **kwargs):
        return Post.objects.all()
    
    def resolve_all_comments(self, info, **kwargs):
        return Comment.objects.all()
    
    def resolve_all_likes(self, info, **kwargs):
        return Like.objects.all()
    
    def resolve_all_shares(self, info, **kwargs):
        return Share.objects.all()

# Mutations
class CreatePost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        # Note: Image upload is not directly supported in GraphQL
        # We would need to implement a separate endpoint for that

    post = graphene.Field(PostType)

    def mutate(self, info, title, content):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to create a post!')
        
        post = Post(
            title=title,
            content=content,
            author=user
        )
        post.save()
        
        return CreatePost(post=post)

class CreateComment(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)
        content = graphene.String(required=True)

    comment = graphene.Field(CommentType)

    def mutate(self, info, post_id, content):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to comment!')
        
        post = Post.objects.get(pk=post_id)
        comment = Comment(
            post=post,
            author=user,
            content=content
        )
        comment.save()
        
        return CreateComment(comment=comment)

class LikePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)

    like = graphene.Field(LikeType)
    
    def mutate(self, info, post_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to like a post!')
        
        post = Post.objects.get(pk=post_id)
        
        # Check if user already liked the post
        like, created = Like.objects.get_or_create(
            post=post,
            user=user
        )
        
        if not created:
            # User already liked this post
            raise Exception('You have already liked this post!')
        
        return LikePost(like=like)

class UnlikePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    def mutate(self, info, post_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to unlike a post!')
        
        try:
            like = Like.objects.get(post_id=post_id, user=user)
            like.delete()
            return UnlikePost(success=True)
        except Like.DoesNotExist:
            return UnlikePost(success=False)

class SharePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)
        shared_with = graphene.String(required=False)

    share = graphene.Field(ShareType)
    
    def mutate(self, info, post_id, shared_with=None):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to share a post!')
        
        post = Post.objects.get(pk=post_id)
        
        share = Share(
            post=post,
            user=user,
            shared_with=shared_with
        )
        share.save()
        
        return SharePost(share=share)

class Mutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    create_comment = CreateComment.Field()
    like_post = LikePost.Field()
    unlike_post = UnlikePost.Field()
    share_post = SharePost.Field() 