# Forwarding launcher for backward compatibility
if __name__ == "__main__":
    import runpy
    runpy.run_module("ml.train_model", run_name="__main__")
