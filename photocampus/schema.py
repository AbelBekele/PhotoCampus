import graphene
import posts.schema

class Query(posts.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we add more apps to our project
    pass

class Mutation(posts.schema.Mutation, graphene.ObjectType):
    # This class will inherit from multiple Mutations
    # as we add more apps to our project
    pass

schema = graphene.Schema(query=Query, mutation=Mutation) 