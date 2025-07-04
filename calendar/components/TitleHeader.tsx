import { Heading } from "@chakra-ui/react";

type Props = { isLargerThan1100: boolean };

export default function TitleHeader({ isLargerThan1100 }: Props) {
  return (
    <>
      <Heading fontSize={isLargerThan1100 ? "72px" : "40px"} fontWeight="900" textAlign="center" pt="30px">
        КАЛЕНДАРЬ ЖИЗНИ
      </Heading>
      <Heading fontSize="12px" fontWeight="800" textAlign="center" pt="15px">
        Время ограничено и ценно, как ты хочешь его провести?
      </Heading>
    </>
  );
}
