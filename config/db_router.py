class RAGRouter:
    rag_apps = {"rag"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.rag_apps:
            return "rag"
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.rag_apps:
            return "rag"
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label in self.rag_apps and obj2._meta.app_label in self.rag_apps:
            return True
        return None

    def allow_migrate(self, db, app_label, **hints):
        if app_label in self.rag_apps:
            return db == "rag"
        return db == "default"
