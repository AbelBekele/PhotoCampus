import graphene
import posts.schema
import organizations.schema
import graphql_jwt

class Query(posts.schema.Query, organizations.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we add more apps to our project
    pass

class Mutation(posts.schema.Mutation, organizations.schema.Mutation, graphene.ObjectType):
    # This class will inherit from multiple Mutations
    # as we add more apps to our project
    
    # JWT Authentication mutations
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation) 