from datetime import datetime
from functools import reduce
from operator import getitem
from pathlib import Path
from py_metrics.utils.json import read_json
from py_metrics.logger import Logger


class ConfigParser:
    def __init__(self, args, options=", "):
        # parse default and custom cli options
        for opt in options:
            args.add_argument(*opt.flags, default=None, type=opt.type)
        args = args.parse_args()
        msg_no_cfg = "Configuration file need to be "
        "specified. Add '-c config.json', for example."
        assert args.config is not None, msg_no_cfg
        self.cfg_fname = Path(args.config)

        config = read_json(self.cfg_fname)
        self._config = self._config = _update_config(config, options, args)

        self.logger = Logger()
        save_dir = Path(self.config['save_dir'])
        timestamp = datetime.now().strftime(r'%m%d_%H%M%S')
        exper_name = self.config['name']
        self._log_dir = save_dir / 'log' / exper_name / timestamp
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger.config_py_logger(self.log_dir)

    def initialize(self, module, module_config, *args, **kwargs):
        """finds a function handle with the name given
          as "type" in config, and returns the
          instance initialized with corresponding
          keyword args given as "args".
        """
        module_name = module_config["type"]
        if "args" in module_config:
            module_args = dict(module_config["args"])
        else:
            module_args = {}
        assert all([k not in module_args for k in kwargs]
                   ), "Overwriting kwargs given in config file is not allowed"
        module_args.update(kwargs)
        return getattr(module, module_name)(*args, **module_args)

    def get_logger(self, name, verbosity=3):
        if not self.logger:
            raise("Please initialize logger.")

        logger = self.logger.get_py_logger(name, verbosity)
        return logger

    def __getitem__(self, name):
        return self.config[name]

    @property
    def config(self):
        return self._config

    @property
    def log_dir(self):
        return self._log_dir


# helper functions used to update config dict with custom cli options
def _update_config(config, options, args):
    for opt in options:
        value = getattr(args, _get_opt_name(opt.flags))
        if value is not None:
            _set_by_path(config, opt.target, value)
    return config


def _get_opt_name(flags):
    for flg in flags:
        if flg.startswith("--"):
            return flg.replace("--", "")
    return flags[0].replace("--", "")


def _set_by_path(tree, keys, value):
    """Set a value in a nested object in tree by sequence of keys."""
    _get_by_path(tree, keys[:-1])[keys[-1]] = value


def _get_by_path(tree, keys):
    """Access a nested object in tree by sequence of keys."""
    return reduce(getitem, keys, tree)
