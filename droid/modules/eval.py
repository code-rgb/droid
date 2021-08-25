import inspect
import os
import re
import sys
import traceback
from io import StringIO
from typing import Any, Tuple

import pyrogram
from meval import meval

from .. import mod, utils
from ..decor import OnCmd


class Eval(mod.Module):
    @OnCmd("evil", owner_only=True)
    async def on_message(self, ctx):
        code = ctx.msg.text[6:] if ctx.msg else None
        if not code:
            return await ctx.reply("Give me code to evaluate.")

        out_buf = StringIO()

        async def _eval() -> Tuple[str, str]:
            async def send(*args: Any, **kwargs: Any) -> pyrogram.types.Message:
                return await ctx.msg.reply(*args, **kwargs)

            def _print(*args: Any, **kwargs: Any) -> None:
                if "file" not in kwargs:
                    kwargs["file"] = out_buf

                return print(*args, **kwargs)

            eval_vars = {
                # Contextual info
                "self": self,
                "ctx": ctx,
                "bot": self.bot,
                "loop": self.bot.loop,
                "client": self.bot.client,
                "plugins": self.bot.plugins,
                "stdout": out_buf,
                # Convenience aliases
                "msg": ctx.msg,
                "message": ctx.msg,
                # Helper functions
                "send": send,
                "print": _print,
                # Built-in modules
                "inspect": inspect,
                "os": os,
                "re": re,
                "sys": sys,
                "traceback": traceback,
                # Third-party modules
                "pyrogram": pyrogram,
                # Custom modules
                "utils": utils,
            }

            try:
                return "", await meval(code, globals(), **eval_vars)
            except Exception as e:  # skipcq: PYL-W0703
                # Find first traceback frame involving the snippet
                first_snip_idx = -1
                tb = traceback.extract_tb(e.__traceback__)
                for i, frame in enumerate(tb):
                    if frame.filename == "<string>" or frame.filename.endswith(
                        "ast.py"
                    ):
                        first_snip_idx = i
                        break

                # Re-raise exception if it wasn't caused by the snippet
                if first_snip_idx == -1:
                    raise e

                # Return formatted stripped traceback
                stripped_tb = tb[first_snip_idx:]
                formatted_tb = utils.format_exception(e)
                await ctx.reply(f"⚠️ Error executing snippet\n\n`{formatted_tb}`")
                return

        prefix, result = await _eval()

        # Always write result if no output has been collected thus far
        if not out_buf.getvalue() or result is not None:
            print(result, file=out_buf)

        out = out_buf.getvalue()
        # Strip only ONE final newline to compensate for our message formatting
        if out.endswith("\n"):
            out = out[:-1]
        if not out:
            return
        await ctx.reply(
            f"""{prefix}**>**
```{code}```

**>>**
```{out}```
"""
        )
