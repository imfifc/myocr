import re
from collections import UserString

from typing import List, Optional, Union


class ScoreString(UserString):
    def __init__(self, text: str, scores: List[float]):
        """

        Args:
            text: 文本
            scores: 每一个字符串对应的置信度，如果和 text 的长度不一致会进行以下操作
                比 text 长：以 text 的 length 为准做阶段
                比 text 短：append text score 的均值，使其和 text 长度相等
        """
        super().__init__(text)
        self.scores = self._new_scores(scores, text)

    def __getitem__(self, index) -> "ScoreString":
        return self.__class__(self.data[index], self.scores[index])

    def __add__(self, other: Union["ScoreString"]) -> "ScoreString":
        return self.__class__(self.data + other.data, self.scores + other.scores)

    def lower(self) -> "ScoreString":
        return self.__class__(self.data.lower(), self.scores)

    def upper(self) -> "ScoreString":
        return self.__class__(self.data.upper(), self.scores)

    def replace(
        self,
        old: Union[str, UserString],
        new: Union[str, UserString],
        count: int = None,
        thresh: float = None,
    ) -> "ScoreString":
        """
        Args:
            old: 旧字符串
            new: 新字符串。
                如果 len(new) > old
                如果 len(new) < old:
                如果 len(new) == old: scores 不变
            count: 最多替换几个
            thresh: 只有当被替换的字符串的 score 小于该阈值时，才会被过滤掉。
                    如果 old 字符串的长度大于 1，则会使用均值来判断
        """
        if isinstance(old, UserString):
            old = old.data
        if isinstance(new, UserString):
            new = new.data
        # 这里的行为和原始的 str.replace() 不一致，原始的行为如下
        # a = "123"
        # a.replace("", "a") -> "a1a2a3"
        if old == "":
            return self.__class__(self.data, scores=self.scores)

        if thresh is None:
            thresh = float("inf")
        else:
            assert 0 <= thresh <= 1

        if count is None:
            count = float("inf")
        assert count >= 0

        iters = re.finditer(re.escape(old), self.data)

        content = ""
        scores = []
        filtered_count = 0
        idx = 0
        for i, m in enumerate(iters):
            start = m.start(0)
            end = m.end(0)
            old_mean_score = self._mean_score(start, end)

            if old_mean_score <= thresh:
                # 需要被替换
                if filtered_count >= count:
                    break

                filtered_count += 1

                content += self.data[idx:start] + new
                scores.extend(
                    self.scores[idx:start]
                    + self._new_scores(self.scores[start:end], new)
                )
            else:
                # 不需要被替换
                content += self.data[idx:end]
                scores.extend(self.scores[idx:end])
            idx = end

        content += self.data[idx:]
        scores.extend(self.scores[idx:])

        return self.__class__(content, scores)

    def keep_digit(self) -> "ScoreString":
        """
        只保留 数字
        """
        content = ""
        scores = []
        for c, s in zip(self.data, self.scores):
            if str.isdigit(c):
                content += c
                scores.append(s)
        return self.__class__(content, scores)

    def _mean_score(self, start, end) -> float:
        count = len(self.scores[start:end])
        if count == 0:
            return 0
        return sum(self.scores[start:end]) / count

    def _new_scores(
        self, old_scores: List[float], new: Union[str, UserString]
    ) -> List[float]:
        """
        根据 old_scores，返回一组长度和 new 一样的分数

        Args:
            old_scores:
            new:
                如果 len(new) > len(old_scores)
                如果 len(new) < len(old_scores):
                如果 len(new) == len(old_scores): scores 不变

        Returns:

        """
        if len(old_scores) == len(new):
            return old_scores.copy()

        if len(old_scores) > len(new):
            # TODO 修改返回策略
            return old_scores[: len(new)].copy()

        if len(old_scores) < len(new):
            # TODO 修改返回策略
            if len(old_scores) == 0:
                return [1] * len(new)
            else:
                mean = sum(old_scores) / len(old_scores)
                return old_scores + [mean] * (len(new) - len(old_scores))


if __name__ == "__main__":
    d = ScoreString("Test123", [1, 2, 3, 4, 5, 6, 7])
