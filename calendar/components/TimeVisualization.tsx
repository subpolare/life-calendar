import { Box, Flex, Text } from "@chakra-ui/layout";
import { defaultSideLabelStyles } from "../constants";
import Circle from "./Circle";
const SECONDS_IN_ONE_WEEK = 60 * 60 * 24 * 7;

type Props = {
  isLargerThan1100: boolean;
  yearToHex: (year: number) => string;
  birthDay: Date;
};

export default function TimeVisualization({
  isLargerThan1100,
  yearToHex,
  birthDay,
}: Props) {
  const monthsOrWeeks = isLargerThan1100 ? 52 : 12;
  const weekAccuracyOffset = monthsOrWeeks === 52 ? 0.1429 : 0; // There are 52.1429 weeks in a year, so offset is used to improve accuracy. If months are being shown instead of weeks, then no offset is used because there are exactly 12 months in a year.

  const weeks = Math.round(
    (new Date().getTime() - birthDay.getTime()) / 1000 / SECONDS_IN_ONE_WEEK
  );

  return (
    <Box
      display="flex"
      flexDirection="row"
      justifyContent={isLargerThan1100 ? "initial" : "center"}
      pl={isLargerThan1100 ? "0px" : "30px"}
    >
      <Flex direction="column">
        {new Array(101).fill(0).map((_, idx1) => (
          <Flex mt="2px" maxW="936px" key={`YEAR ${idx1}`}>
            <Box ml="-25px" textAlign="center" position="absolute">
              <Text
                fontWeight="900"
                w="17.7px"
                fontSize="9px"
                key={"Num" + idx1}
              >
                {idx1}
              </Text>
            </Box>
            {new Array(monthsOrWeeks).fill(0).map((_, idx2) => (
              <Box
                w={936 / 52 - 2.5 + "px"}
                mr="2px"
                key={`YEAR ${idx1} WEEK ${idx2 + 1}`}
              >
                <Circle
                  size="15"
                  outline={yearToHex(idx1)}
                  isFilled={
                    idx1 * (monthsOrWeeks + weekAccuracyOffset) + idx2 + 1 <
                    weeks / (isLargerThan1100 ? 1 : 13 / 3)
                  }
                />
              </Box>
            ))}
          </Flex>
        ))}
      </Flex>
      <Flex direction="column" w="30px">
        <Text
          {...defaultSideLabelStyles}
          ml="-50px"
          mt="110px"
          w="120px"
          color={yearToHex(12)}
        >
          Детство (0–12 лет)
        </Text>
        <Text
          {...defaultSideLabelStyles}
          ml="-63px"
          mt="165px"
          w="150px"
          color={yearToHex(19)}
        >
          Подростки (13–19 лет)
        </Text>
        <Text
          {...defaultSideLabelStyles}
          ml="-76px"
          mt="170px"
          w="175px"
          color={yearToHex(34)}
        >
          Ранняя взрослость (20–34 лет)
        </Text>
        <Text
          {...defaultSideLabelStyles}
          ml="-76px"
          mt="240px"
          w="175px"
          color={yearToHex(49)}
        >
          Средняя взрослость (35–49 лет)
        </Text>
        <Text
          {...defaultSideLabelStyles}
          ml="-76px"
          mt="365px"
          w="175px"
          color={yearToHex(79)}
        >
          Зрелая взрослость (50–79 лет)
        </Text>
        <Text
          {...defaultSideLabelStyles}
          ml="-76px"
          mt="430px"
          w="175px"
          color={yearToHex(100)}
        >
          Поздняя взрослость (80–100 лет)
        </Text>
      </Flex>
    </Box>
  );
}
